import cv2
import numpy as np
import pyautogui
import mss
import time
import keyboard
import random
from collections import deque
import threading

class SnakeAutoPlayer:
    def __init__(self):
        # 游戏窗口标题
        self.game_window_title = "贪吃蛇游戏"
        # 颜色阈值 (HSV)
        self.color_thresholds = {
            'food': ([0, 120, 120], [10, 255, 255]),  # 红色食物
            'snake_head': ([100, 150, 0], [140, 255, 255]),  # 蓝色蛇头
            'snake_body': ([40, 40, 40], [70, 255, 255])  # 绿色蛇身
        }
        # 游戏网格参数
        self.grid_size = 20
        # 控制方向
        self.directions = {
            'up': (0, -1),
            'down': (0, 1),
            'left': (-1, 0),
            'right': (1, 0)
        }
        self.current_direction = 'right'
        self.next_direction = 'right'
        # 游戏状态
        self.running = False
        self.game_over = False
        # 初始化游戏窗口位置
        self.window_rect = None
        self.find_game_window()

    def find_game_window(self):
        """查找游戏窗口位置"""
        windows = pyautogui.getWindowsWithTitle(self.game_window_title)
        if windows:
            self.window_rect = windows[0]
            self.window_rect.activate()
            time.sleep(1)  # 等待窗口激活
            print(f"找到游戏窗口: {self.window_rect.title}")
            print(f"窗口位置: {self.window_rect.left}, {self.window_rect.top}, {self.window_rect.width}, {self.window_rect.height}")
        else:
            raise Exception(f"未找到标题为'{self.game_window_title}'的窗口")

    def capture_game_screen(self):
        """捕获游戏屏幕"""
        with mss.mss() as sct:
            monitor = {
                'top': self.window_rect.top + 30,  # 调整以排除窗口标题栏
                'left': self.window_rect.left,
                'width': self.window_rect.width,
                'height': self.window_rect.height
            }
            screenshot = sct.grab(monitor)
            # 转换为OpenCV格式
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img

    def detect_game_objects(self, img):
        """检测游戏对象（蛇头、蛇身、食物）"""
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        objects = {
            'snake_head': None,
            'snake_body': [],
            'food': None
        }

        # 检测蛇头
        lower, upper = self.color_thresholds['snake_head']
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            # 找到最大的轮廓（蛇头）
            max_contour = max(contours, key=cv2.contourArea)
            moments = cv2.moments(max_contour)
            if moments['m00'] > 0:
                cx = int(moments['m10'] / moments['m00'])
                cy = int(moments['m01'] / moments['m00'])
                # 转换为网格坐标
                grid_x = cx // self.grid_size
                grid_y = cy // self.grid_size
                objects['snake_head'] = (grid_x, grid_y)

        # 检测蛇身
        lower, upper = self.color_thresholds['snake_body']
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            if cv2.contourArea(contour) > 10:
                moments = cv2.moments(contour)
                if moments['m00'] > 0:
                    cx = int(moments['m10'] / moments['m00'])
                    cy = int(moments['m01'] / moments['m00'])
                    grid_x = cx // self.grid_size
                    grid_y = cy // self.grid_size
                    objects['snake_body'].append((grid_x, grid_y))

        # 检测食物
        lower, upper = self.color_thresholds['food']
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            max_contour = max(contours, key=cv2.contourArea)
            moments = cv2.moments(max_contour)
            if moments['m00'] > 0:
                cx = int(moments['m10'] / moments['m00'])
                cy = int(moments['m01'] / moments['m00'])
                grid_x = cx // self.grid_size
                grid_y = cy // self.grid_size
                objects['food'] = (grid_x, grid_y)

        return objects

    def bfs_shortest_path(self, start, end, obstacles, grid_width, grid_height):
        """使用BFS寻找最短路径，增加安全性检查"""
        if start == end:
            return []

        # 定义四个方向
        directions = [ (0, -1), (0, 1), (-1, 0), (1, 0) ]
        queue = deque([(start, [start])])
        visited = set([start])

        while queue:
            current, path = queue.popleft()

            for dx, dy in directions:
                next_node = (current[0] + dx, current[1] + dy)
                # 检查是否在网格内
                if 0 <= next_node[0] < grid_width and 0 <= next_node[1] < grid_height:
                    # 检查是否是目标或可移动区域
                    if next_node == end:
                        return path + [next_node]
                    if next_node not in visited and next_node not in obstacles:
                        # 额外检查：确保这个位置周围有足够空间
                        safe = True
                        for ndx, ndy in directions:
                            check_node = (next_node[0] + ndx, next_node[1] + ndy)
                            if check_node in obstacles or not (0 <= check_node[0] < grid_width and 0 <= check_node[1] < grid_height):
                                safe = False
                                break
                        if safe or len(path) < 3:  # 允许短路径冒险
                            visited.add(next_node)
                            queue.append((next_node, path + [next_node]))

        # 如果找不到直接路径，尝试寻找安全区域
        safe_zones = []
        for x in range(grid_width):
            for y in range(grid_height):
                pos = (x, y)
                if pos not in visited and pos not in obstacles:
                    # 计算与食物的距离和周围空间
                    distance = abs(x - end[0]) + abs(y - end[1])
                    space_score = 0
                    for dx, dy in directions:
                        check_node = (x + dx, y + dy)
                        if check_node not in obstacles and 0 <= check_node[0] < grid_width and 0 <= check_node[1] < grid_height:
                            space_score += 1
                    # 优先选择距离近且空间大的区域
                    safe_zones.append((distance - space_score * 0.5, pos))

        # 选择最近的安全区域
        if safe_zones:
            safe_zones.sort()
            safest_pos = safe_zones[0][1]
            # 重新BFS寻找前往安全区域的路径
            queue = deque([(start, [start])])
            visited = set([start])
            while queue:
                current, path = queue.popleft()
                for dx, dy in directions:
                    next_node = (current[0] + dx, current[1] + dy)
                    if 0 <= next_node[0] < grid_width and 0 <= next_node[1] < grid_height:
                        if next_node == safest_pos:
                            return path + [next_node]
                        if next_node not in visited and next_node not in obstacles:
                            visited.add(next_node)
                            queue.append((next_node, path + [next_node]))

        return None  # 找不到路径

    def determine_direction(self, game_objects):
        """确定下一步移动方向"""
        if not all([game_objects['snake_head'], game_objects['food']]):
            return self.current_direction

        head = game_objects['snake_head']
        food = game_objects['food']
        body = game_objects['snake_body']

        # 计算网格尺寸
        grid_width = self.window_rect.width // self.grid_size
        grid_height = self.window_rect.height // self.grid_size

        # 检查前方是否有障碍物
        current_dir_vector = self.directions[self.current_direction]
        next_pos = (head[0] + current_dir_vector[0], head[1] + current_dir_vector[1])
        if next_pos in body or not (0 <= next_pos[0] < grid_width and 0 <= next_pos[1] < grid_height):
            # 前方有障碍物，需要改变方向
            possible_dirs = []
            for dir_name, dir_vector in self.directions.items():
                if dir_name == self.get_opposite_direction(self.current_direction):
                    continue
                new_pos = (head[0] + dir_vector[0], head[1] + dir_vector[1])
                if new_pos not in body and 0 <= new_pos[0] < grid_width and 0 <= new_pos[1] < grid_height:
                    possible_dirs.append(dir_name)
            if possible_dirs:
                return random.choice(possible_dirs)
            else:
                # 所有方向都有障碍物，尝试掉头
                return self.get_opposite_direction(self.current_direction)

        # 使用BFS寻找最短路径
        path = self.bfs_shortest_path(head, food, body, grid_width, grid_height)

        if not path or len(path) < 2:
            # 如果找不到路径，尝试随机移动
            possible_dirs = list(self.directions.keys())
            possible_dirs.remove(self.get_opposite_direction(self.current_direction))
            # 过滤掉会导致碰撞的方向
            safe_dirs = []
            for dir_name in possible_dirs:
                dir_vector = self.directions[dir_name]
                new_pos = (head[0] + dir_vector[0], head[1] + dir_vector[1])
                if new_pos not in body and 0 <= new_pos[0] < grid_width and 0 <= new_pos[1] < grid_height:
                    safe_dirs.append(dir_name)
            if safe_dirs:
                return random.choice(safe_dirs)
            else:
                return self.current_direction

        # 根据路径确定下一步方向
        next_pos = path[1]
        dx = next_pos[0] - head[0]
        dy = next_pos[1] - head[1]

        if dx == 1:
            return 'right'
        elif dx == -1:
            return 'left'
        elif dy == 1:
            return 'down'
        elif dy == -1:
            return 'up'

        return self.current_direction

    def get_opposite_direction(self, direction):
        """获取相反方向"""
        opposites = {
            'up': 'down',
            'down': 'up',
            'left': 'right',
            'right': 'left'
        }
        return opposites[direction]

    def execute_move(self, direction):
        """执行移动命令"""
        # 避免直接反向移动
        if direction == self.get_opposite_direction(self.current_direction):
            direction = self.current_direction

        # 只有方向改变时才发送按键
        if direction != self.current_direction:
            key_map = {
                'up': 'up',
                'down': 'down',
                'left': 'left',
                'right': 'right'
            }
            pyautogui.press(key_map[direction])
            self.current_direction = direction
            print(f"移动方向: {direction}")

    def check_game_over(self, img, food_pos=None):
        """检查游戏是否结束"""
        # 检测红色的"游戏结束"文字
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # 扩大红色检测范围
        lower_red1 = np.array([0, 120, 120])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 120, 120])
        upper_red2 = np.array([180, 255, 255])
        
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)

        # 如果有食物位置，排除食物区域
        if food_pos:
            try:
                # 创建一个掩码，排除食物位置
                food_mask = np.zeros(mask.shape, np.uint8)
                # 转换食物位置到图像坐标
                food_x = food_pos[0] * self.grid_size
                food_y = food_pos[1] * self.grid_size
                # 绘制食物区域的矩形掩码
                cv2.rectangle(food_mask, (food_x, food_y), 
                              (food_x + self.grid_size, food_y + self.grid_size), 255, -1)
                # 从原始掩码中减去食物区域
                mask = cv2.subtract(mask, food_mask)
            except Exception as e:
                print(f"排除食物区域时出错: {e}")

        # 计算红色区域面积
        red_area = cv2.countNonZero(mask)
        # 只有当红色面积足够大且连续时才判断为游戏结束
        if red_area > 1200:
            # 检查是否有"游戏结束"文字的轮廓
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                if cv2.contourArea(contour) > 1000:
                    # 进一步验证轮廓形状，排除圆形食物
                    perimeter = cv2.arcLength(contour, True)
                    if perimeter > 0:
                        circularity = 4 * np.pi * cv2.contourArea(contour) / (perimeter * perimeter)
                        if circularity < 0.7:  # 文字轮廓不会是圆形
                            return True
        return False

    def run(self):
        """运行自动游戏"""
        self.running = True
        print("自动游戏开始! 按F12停止")

        # 注册停止按键
        keyboard.add_hotkey('f12', self.stop)

        try:
            while self.running:
                # 捕获游戏画面
                img = self.capture_game_screen()

                # 检测游戏对象
                game_objects = self.detect_game_objects(img)

                # 检查游戏是否结束
                if not self.game_over:
                    self.game_over = self.check_game_over(img, game_objects.get('food'))

                if self.game_over:
                    print("游戏结束!")
                    # 按R键重新开始
                    pyautogui.press('r')
                    time.sleep(1.5)  # 增加等待时间确保游戏重启完成
                    self.game_over = False
                    continue

                # 确定移动方向
                direction = self.determine_direction(game_objects)

                # 执行移动
                self.execute_move(direction)

                # 控制游戏速度
                time.sleep(0.01)  # 稍微增加延迟，给游戏足够响应时间

        except Exception as e:
            print(f"发生错误: {e}")
        finally:
            self.running = False
            print("自动游戏已停止")

    def stop(self):
        """停止自动游戏"""
        self.running = False

if __name__ == "__main__":
    auto_player = SnakeAutoPlayer()
    auto_player.run()