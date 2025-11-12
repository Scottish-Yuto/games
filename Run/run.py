import pygame
import random
import sys

# Pygameの初期化
pygame.init()

# 画面設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Gothic Dark Runner")

# 色の定義（ゴシック/ダークな世界観を意識）
BLACK = (10, 10, 15)
WHITE = (240, 240, 250)
RED = (150, 50, 50)
GREEN = (50, 150, 50)
GROUND_COLOR = (25, 25, 35)
# ★追加: 障害物（球で倒せない）の色
OBSTACLE_COLOR = GROUND_COLOR

# フレームレート
FPS = 60
clock = pygame.time.Clock()

# スコア
score = 0
font = pygame.font.Font(None, 36)

GAME_SPEED = 7

class Player(pygame.sprite.Sprite):
    """
    Playerのクラス
    """
    def __init__(self):
        super().__init__()
        self.size = 50
        # プレイヤーを四角形として描画
        self.image = pygame.Surface([self.size, self.size])
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.x = 50
        self.rect.y = SCREEN_HEIGHT - self.size - 40 # 地面より上に配置
        
        self.vel_y = 0
        self.is_jumping = False
        self.on_ground = True
        self.gravity = 1
        self.jump_strength = 20
        
        # ★追加: 二段ジャンプ用のカウンタ
        self.jump_count = 0
        self.MAX_JUMPS = 2

    def update(self):
        # 重力とジャンプの処理
        if not self.on_ground:
            self.vel_y += self.gravity
        self.rect.y += self.vel_y

        # 地面との衝突判定 (仮の地面 y = SCREEN_HEIGHT - 40)
        if self.rect.bottom >= SCREEN_HEIGHT - 40:
            self.rect.bottom = SCREEN_HEIGHT - 40
            self.vel_y = 0
            self.is_jumping = False
            self.on_ground = True
            self.jump_count = 0
            # ★修正: 地面についたらジャンプ回数をリセット
        else:
            self.on_ground = False

    def jump(self):
        # ★修正: ジャンプ回数が MAX_JUMPS 未満の場合にジャンプを許可
        if self.jump_count < self.MAX_JUMPS:
            self.is_jumping = True
            self.vel_y = -self.jump_strength
            self.on_ground = False
            # ★修正: ジャンプ回数をインクリメント
            self.jump_count += 1

class Enemy(pygame.sprite.Sprite):
    """
    Enemyのクラス
    """
    def __init__(self, x):
        super().__init__()
        self.size = random.randint(30, 60) # サイズをランダムに
        # エネミーを四角形として描画 (球で倒せる)
        self.image = pygame.Surface([self.size, self.size])
        self.image.fill(GREEN)

        # ★修正: エネミーに目をシンプルなドットで描画する処理
        dot_size = max(2, self.size // 10) # 目のドットのサイズ (エネミーサイズに応じて調整、最低2px)
        eye_color = WHITE # 目の色

        # 目の位置 (エネミーの画像Surface内での相対座標)
        # エネミーの右上に2つのドットの目を配置
        # ドットなので中心ではなく左上座標を指定
        offset_x = self.size // 4 # X座標オフセット (エネミー幅の1/4)
        offset_y = self.size // 4 # Y座標オフセット (エネミー高さの1/4)
        
        # 左目 (ドット)
        pygame.draw.rect(self.image, eye_color, (offset_x, offset_y, dot_size, dot_size))

        # 右目 (ドット)
        pygame.draw.rect(self.image, eye_color, (self.size - offset_x - dot_size, offset_y, dot_size, dot_size))
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = SCREEN_HEIGHT - self.size - 40

    def update(self):
        self.rect.x -= GAME_SPEED
        # 画面外に出たら削除
        if self.rect.right < 0:
            self.kill()

class Obstacle(pygame.sprite.Sprite):
    """
    弾丸で倒せない障害物のクラス
    """
    def __init__(self, x):
        super().__init__()
        self.size = random.randint(40, 70) # エネミーより少し大きくする
        # 障害物を四角形として描画 (球で倒せない)
        self.image = pygame.Surface([self.size, self.size])
        self.image.fill(OBSTACLE_COLOR)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = SCREEN_HEIGHT - self.size - 40

    def update(self):
        self.rect.x -= GAME_SPEED
        # 画面外に出たら削除
        if self.rect.right < 0:
            self.kill()

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.size = 10
        # 弾丸を円として描画
        self.image = pygame.Surface([self.size, self.size])
        self.image.set_colorkey(BLACK) # 背景を透明に
        pygame.draw.circle(self.image, WHITE, (self.size // 2, self.size // 2), self.size // 2)
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 15

    def update(self: 'Bullet'):
        self.rect.x += self.speed
        # 画面外に出たら削除
        if self.rect.left > SCREEN_WIDTH:
            self.kill()

# スプライトグループの作成
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
# ★追加: 障害物用のグループ
obstacles = pygame.sprite.Group() 

# プレイヤーの作成
player = Player()
all_sprites.add(player)

# エネミー生成タイマー（ランダム配置用）
ENEMY_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(ENEMY_EVENT, 0) # タイマーを停止 (0に設定)

# ランダムな生成間隔の設定
MIN_SPAWN_TIME = 800  # 最小生成間隔 (ミリ秒)
MAX_SPAWN_TIME = 2000 # 最大生成間隔 (ミリ秒)

def set_random_timer():
    """次のハザード生成までの時間をランダムに設定する関数"""
    spawn_time = random.randint(MIN_SPAWN_TIME, MAX_SPAWN_TIME)
    pygame.time.set_timer(ENEMY_EVENT, spawn_time, 1) # 1回だけ実行するよう設定 (引数 loop=1)

set_random_timer()

def draw_text(surface, text, x, y, align='center'):
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect()
    # alignパラメータを追加し、中央寄せに対応
    if align == 'center':
        text_rect.center = (x, y) 
    elif align == 'right':
        text_rect.topright = (x, y)
    else: # 'left'
        text_rect.topleft = (x, y)
        
    surface.blit(text_surface, text_rect)

def game_loop():
    global score
    global GAME_SPEED
    running = True
    game_over = False

    # リスタート時に速度をリセット
    GAME_SPEED = 7
    
    # プレイヤーの再作成 (リスタート時に備えて)
    global player
    # 既存のスプライトグループをクリア
    all_sprites.empty()
    enemies.empty()
    bullets.empty()
    obstacles.empty() # ★障害物グループもクリア
    
    player = Player()
    all_sprites.add(player)
    score = 0

    while running:
        # フレームレートの設定
        clock.tick(FPS)

        # 1. イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # リスタート処理
            if game_over and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN: # ENTERキーでリスタート
                    set_random_timer()
                    return True 
            
            # ゲームオーバーでない場合のみ操作を受け付ける
            if not game_over:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w or event.key == pygame.K_UP:
                         player.jump()
                    if event.key == pygame.K_SPACE:
                        bullet = Bullet(player.rect.right, player.rect.centery)
                        all_sprites.add(bullet)
                        bullets.add(bullet)

                # ランダムエネミー生成（エネミーか障害物をランダムに生成）
                if event.type == ENEMY_EVENT:
                   # 発生確率の設定
                    ENEMY_CHANCE = 0.30  # エネミーの出現確率 (30%)
                    
                    # 乱数を生成し、確率に基づいてどちらを生成するか決定
                    if random.random() < ENEMY_CHANCE:
                        # 30%の確率でEnemyを生成
                        new_hazard = Enemy(SCREEN_WIDTH + random.randint(50, 200))
                        enemies.add(new_hazard)
                    else:
                        # 70%の確率でObstacleを生成
                        new_hazard = Obstacle(SCREEN_WIDTH + random.randint(50, 200))
                        obstacles.add(new_hazard)
                        
                    all_sprites.add(new_hazard) # どちらもall_spritesに追加
                    set_random_timer()

            # ゲームオーバー時の描画と処理スキップ
            if game_over:
                SCREEN.fill(BLACK)
                # ★修正: 画面の中心座標を使用し、y座標を調整して中央寄せを適用
                center_x = SCREEN_WIDTH // 2
                center_y = SCREEN_HEIGHT // 2
                draw_text(SCREEN, "GAME OVER", center_x, center_y - 50, align='center')
                draw_text(SCREEN, f"Final Score: {score}", center_x, center_y, align='center')
                draw_text(SCREEN, "- Press ENTER to Restart -", center_x, center_y + 50, align='center')
                pygame.display.flip()
                continue 

        # 2. オブジェクトの更新
        all_sprites.update()
        if not game_over:
            score += 1 # 走っている間、スコアが増加

        # スコアが一定値に達するごとに速度を上げる (難易度調整)
        if score > 0 and score % 1000 == 0 and GAME_SPEED < 15:
            GAME_SPEED += 0.5 
            print(f"Speed increased to: {GAME_SPEED}")

        # 3. 衝突判定

        # プレイヤーとハザードの衝突（エネミーと障害物を両方チェック）
        # 複数のグループをまとめて衝突判定するために一時的なグループを作成
        all_hazards = enemies.copy()
        all_hazards.add(obstacles)
        
        hits = pygame.sprite.spritecollide(player, all_hazards, False)
        
        for hit in hits:
            # 踏みつけ判定
            if player.vel_y > 0:
                # 踏みつけ成功
                
                if isinstance(hit, Enemy):
                    player.vel_y = -10 # 少し跳ね返る
                    score += 100 # スコア加算
                    hit.kill() # エネミーは踏みつけで破壊

                elif isinstance(hit, Obstacle):
                    # 障害物を踏んだ場合: バウンドせず、破壊しない
                    # プレイヤーを障害物の上にぴったり配置し、下降速度をゼロにする
                    player.rect.bottom = hit.rect.top
                    player.vel_y = 0
                    player.on_ground = True # 地面判定を一時的にTrueに
                
                player.jump_count = 0
                
            else:
                # 側面衝突（ゲームオーバー）
                # game_overになる瞬間に一度だけprintし、その後 break の直前で print するのを防ぐために条件を追加
                if not game_over: # ★追加: まだゲームオーバーになっていない場合のみ実行
                    print(f"Game Over! Final Score: {score}")
                game_over = True
                break # ゲームオーバーになったら他の衝突チェックをスキップ

        if game_over:
            continue # ゲームオーバーフラグが立ったら、弾丸衝突チェックをスキップ

        # 弾丸の衝突
        bullet_hits = pygame.sprite.groupcollide(bullets, enemies, True, True)

        # 弾丸がエネミーに当たった場合
        for bullet, enemy_list in bullet_hits.items():
            for enemy in enemy_list:
                score += 50 # スコア加算

        pygame.sprite.groupcollide(bullets, obstacles, True, False)

        # 4. 描画
        SCREEN.fill(BLACK) # 背景を暗い色で塗りつぶし

        # 地面の描画
        pygame.draw.rect(SCREEN, GROUND_COLOR, (0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40))
        
        # すべてのスプライトを描画
        all_sprites.draw(SCREEN)

        # スコア表示
        draw_text(SCREEN, f"SCORE: {score}", 10, 10, align='left')

        # 画面の更新
        pygame.display.flip()

    # ゲーム終了
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    # リスタートループを追加
    while True:
        if not game_loop():
            break