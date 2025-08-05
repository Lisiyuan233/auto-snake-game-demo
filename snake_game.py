import pygame
import random
import sys

# 初始化pygame
pygame.init()

# 游戏常量
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
HEAD_COLOR = BLUE  # 蛇头颜色

# 设置窗口
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("贪吃蛇游戏")

# 时钟控制游戏速度
clock = pygame.time.Clock()
FPS = 30

class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        self.length = 1
        self.positions = [(WIDTH // 2, HEIGHT // 2)]
        self.direction = random.choice([(0, -1), (0, 1), (-1, 0), (1, 0)])
        self.color = GREEN
        self.score = 0

    def get_head_position(self):
        return self.positions[0]

    def turn(self, point):
        if self.length > 1 and (point[0] * -1, point[1] * -1) == self.direction:
            return
        else:
            self.direction = point

    def move(self):
        head = self.get_head_position()
        x, y = self.direction
        new_x = (head[0] + (x * GRID_SIZE)) % WIDTH
        new_y = (head[1] + (y * GRID_SIZE)) % HEIGHT
        
        # 检测是否撞到自己
        body_set = set(self.positions[2:])
        if (new_x, new_y) in body_set:
            self.reset()
            return True
        
        self.positions.insert(0, (new_x, new_y))
        if len(self.positions) > self.length:
            self.positions.pop()
        return False

    def draw(self, surface):
        for i, p in enumerate(self.positions):
            rect = pygame.Rect((p[0], p[1]), (GRID_SIZE - 1, GRID_SIZE - 1))
            # 蛇头使用不同颜色
            color = HEAD_COLOR if i == 0 else self.color
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, WHITE, rect, 1)

class Food:
    def __init__(self):
        self.position = (0, 0)
        self.color = RED
        self.randomize_position()

    def randomize_position(self):
        self.position = (
            random.randint(0, GRID_WIDTH - 1) * GRID_SIZE,
            random.randint(0, GRID_HEIGHT - 1) * GRID_SIZE
        )

    def draw(self, surface):
        rect = pygame.Rect((self.position[0], self.position[1]), (GRID_SIZE - 1, GRID_SIZE - 1))
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface, WHITE, rect, 1)

def main():
    snake = Snake()
    food = Food()
    
    # 初始化字体和分数文本
    font = pygame.font.SysFont(None, 36)
    previous_score = 0
    score_text = font.render(f"分数: {previous_score}", True, WHITE)
    
    # 游戏主循环
    running = True
    game_over = False
    
    while running:
        screen.fill(BLACK)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    snake.turn((0, -1))
                elif event.key == pygame.K_DOWN:
                    snake.turn((0, 1))
                elif event.key == pygame.K_LEFT:
                    snake.turn((-1, 0))
                elif event.key == pygame.K_RIGHT:
                    snake.turn((1, 0))
                elif event.key == pygame.K_r and game_over:
                    snake.reset()
                    game_over = False
        
        if not game_over:
            game_over = snake.move()
            
            # 检测是否吃到食物
            if snake.get_head_position() == food.position:
                snake.length += 1
                snake.score += 10
                food.randomize_position()
                
                # 确保食物不会生成在蛇身上
                while food.position in snake.positions:
                    food.randomize_position()
        
        snake.draw(screen)
        food.draw(screen)
        
        # 显示分数
        if snake.score != previous_score:
            score_text = font.render(f"分数: {snake.score}", True, WHITE)
            previous_score = snake.score
        screen.blit(score_text, (10, 10))
        
        # 显示游戏结束信息
        if game_over:
            game_over_text = font.render("游戏结束! 按R键重新开始", True, RED)
            text_rect = game_over_text.get_rect(center=(WIDTH//2, HEIGHT//2))
            screen.blit(game_over_text, text_rect)
        
        pygame.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main()