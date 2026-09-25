# PRD + SRS — PyFight

## 1. Informasi Proyek

**Nama sementara:** `PyFight`  
**Platform:** Desktop  
**Framework:** Python + Pygame  
**Genre:** 2D Fighting / Fighting Game  
**Mode:** 1 vs 1 Player vs Computer  
**Target awal:** Prototype / MVP  

---

# 2. Product Requirement Document (PRD)

## 2.1 Latar Belakang

PyFight merupakan game pertarungan 2D satu lawan satu yang mempertemukan pemain dengan karakter yang dikendalikan oleh komputer.

Pemain dapat mengontrol karakter untuk bergerak, menyerang lawan menggunakan serangan jarak dekat maupun jarak jauh, bertahan, dan mengalahkan komputer sebelum health pemain habis.

Pada tahap awal, karakter menggunakan **mockup sederhana** seperti bentuk persegi/persegi panjang. Aset karakter sebenarnya dapat dimasukkan kemudian tanpa mengubah mekanisme utama game.

## 2.2 Tujuan Produk

Game memiliki tujuan:

1. Membuat prototype fighting game menggunakan Pygame.
2. Menyediakan pertarungan 1 vs 1 antara pemain dan komputer.
3. Menyediakan movement yang responsif.
4. Menyediakan serangan jarak dekat.
5. Menyediakan serangan jarak jauh/projectile.
6. Menyediakan sistem HP dan damage.
7. Menyediakan AI sederhana untuk komputer.
8. Menyediakan main menu.
9. Menyediakan sistem menang/kalah.
10. Memungkinkan penggantian karakter dan sprite di masa depan.

## 2.3 Target Pengguna

- Pemain game desktop.
- Pemula yang ingin memainkan game fighting sederhana.
- Developer yang ingin mempelajari pembuatan game menggunakan Pygame.

---

# 3. Game Flow

```text
START
  │
  ▼
MAIN MENU
  │
  ├── PLAY
  │     │
  │     ▼
  │   FIGHT
  │     │
  │     ├── Player menang
  │     │      │
  │     │      ▼
  │     │   VICTORY
  │     │
  │     └── Computer menang
  │            │
  │            ▼
  │          DEFEAT
  │
  ├── HOW TO PLAY
  │
  └── QUIT
```

---

# 4. Main Menu

Game harus memiliki menu utama.

Contoh tampilan:

```text
╔══════════════════════════════════╗
║                                  ║
║             PYFIGHT              ║
║                                  ║
║           [  PLAY  ]             ║
║       [ HOW TO PLAY ]            ║
║           [ QUIT ]               ║
║                                  ║
╚══════════════════════════════════╝
```

### Fitur

- Game title
- Play
- How to Play
- Quit

Navigasi dapat menggunakan keyboard atau mouse.

Untuk prototype:

```text
↑ / ↓  = memilih menu
ENTER  = memilih
```

---

# 5. How to Play

Menu ini menjelaskan kontrol permainan.

```text
HOW TO PLAY

MOVEMENT
A / D       Move Left / Right
W           Jump
S           Crouch

ATTACK
J           Melee Attack
K           Ranged Attack
L           Block

ESC         Back / Pause
```

Kontrol dapat diubah pada tahap pengembangan berikutnya.

---

# 6. Gameplay

## 6.1 Arena

Pertarungan dilakukan pada arena 2D.

```text
┌─────────────────────────────────────────────┐
│                                             │
│       PLAYER                 COMPUTER       │
│         █                       █           │
│         █                       █           │
│        ███                     ███          │
│                                             │
│─────────────────────────────────────────────│
│                  FLOOR                      │
└─────────────────────────────────────────────┘
```

Arena minimal memiliki:

- Background
- Ground/floor
- Batas kiri
- Batas kanan
- Player
- Enemy

---

# 7. Karakter

Pada tahap prototype, karakter menggunakan mockup.

Contoh:

### Player

```text
    O
   /|\
   / \
```

### Computer

```text
    O
   /|\
   / \
```

Dalam implementasi Pygame, karakter sementara dapat dibuat menggunakan:

- Rectangle
- Circle
- Polygon

Contoh:

```text
Player = warna biru
Enemy  = warna merah
```

Nantinya dapat diganti menjadi sprite:

```text
Player → player.png
Enemy  → enemy.png
```

tanpa mengubah sistem combat.

---

# 8. Sistem Movement

Player dapat:

### Horizontal

```text
A → bergerak kiri
D → bergerak kanan
```

### Jump

```text
W → melompat
```

Karakter memiliki gravitasi dan tidak boleh keluar dari arena.

---

# 9. Sistem Combat

Game memiliki dua tipe serangan utama.

## 9.1 Melee Attack

Serangan jarak dekat.

```text
PLAYER        ENEMY
  █            █
  █───────►    █
```

Melee memiliki:

- Damage
- Attack range
- Cooldown
- Attack animation
- Hit detection

Contoh:

```text
Damage   : 10
Range    : 60 px
Cooldown : 0.5 sec
```

## 9.2 Ranged Attack

Player dapat melakukan serangan jarak jauh menggunakan projectile.

```text
PLAYER                          ENEMY
  █  ────────────────►           █
```

Projectile dapat berupa lingkaran sederhana pada prototype dan sprite khusus pada tahap berikutnya.

Projectile memiliki:

- Damage
- Speed
- Direction
- Lifetime
- Collision detection

Contoh:

```text
Damage = 15
Speed  = 8 px/frame
```

---

# 10. Health System

Masing-masing karakter mempunyai HP.

```text
PLAYER
████████████████████ 100 HP

COMPUTER
████████████████████ 100 HP
```

Ketika terkena serangan:

```text
100 HP
  ↓
90 HP
```

Jika:

```text
HP <= 0
```

maka karakter kalah.

---

# 11. Combat Logic

### Melee

```text
Attack
   ↓
Check Hitbox
   ↓
Enemy terkena?
   │
   ├── NO → tidak terjadi apa-apa
   │
   └── YES
        ↓
    Enemy HP -= Damage
```

### Ranged

```text
K
 ↓
Create Projectile
 ↓
Projectile bergerak
 ↓
Collision dengan Enemy
 ↓
Enemy HP -= Damage
 ↓
Projectile Destroy
```

---

# 12. AI Computer

Computer menggunakan AI sederhana pada versi pertama.

## State AI

```text
IDLE
 │
 ▼
CHECK DISTANCE
 │
 ├── Jauh ──► APPROACH
 │
 ├── Dekat ─► ATTACK
 │
 └── Sangat jauh ─► RANGED ATTACK
```

Contoh aturan:

```text
distance > 300
→ menggunakan ranged attack

100 < distance <= 300
→ mendekati player

distance <= 100
→ menggunakan melee attack
```

Contoh pseudocode:

```python
if distance > 200:
    move_towards_player()

elif distance > 80:
    ranged_attack()

else:
    melee_attack()
```

---

# 13. Victory / Defeat Screen

Jika player menang:

```text
╔══════════════════════════════╗
║                              ║
║          VICTORY!            ║
║                              ║
║        YOU WIN!              ║
║                              ║
║       [ PLAY AGAIN ]         ║
║       [ MAIN MENU ]          ║
║                              ║
╚══════════════════════════════╝
```

Jika player kalah:

```text
╔══════════════════════════════╗
║                              ║
║          DEFEAT              ║
║                              ║
║        YOU LOSE!             ║
║                              ║
║       [ PLAY AGAIN ]         ║
║       [ MAIN MENU ]          ║
║                              ║
╚══════════════════════════════╝
```

---

# 14. Pause

Selama pertandingan:

```text
ESC
```

menampilkan:

```text
┌───────────────────────────┐
│          PAUSED           │
│                           │
│       [ RESUME ]          │
│       [ RESTART ]         │
│       [ MAIN MENU ]       │
└───────────────────────────┘
```

---

# 15. Non-Functional Requirements

## Performance

Target:

- 60 FPS
- Input responsif
- Tidak terjadi lag pada arena normal

## Compatibility

Target awal:

- Windows
- Python 3.x
- Pygame

## Maintainability

Kode dipisahkan berdasarkan fungsi agar mudah dikembangkan.

Contoh:

```text
main.py
player.py
enemy.py
projectile.py
menu.py
game.py
```

---

# 16. Software Requirement Specification (SRS)

## 16.1 Functional Requirements

### FR-01 — Main Menu

Sistem harus menampilkan main menu ketika game dijalankan.

### FR-02 — Start Game

Sistem harus memulai permainan ketika player memilih `PLAY`.

### FR-03 — Player Movement

Sistem harus memungkinkan player bergerak ke kiri dan kanan.

### FR-04 — Jump

Sistem harus memungkinkan player melakukan jump.

### FR-05 — Melee Attack

Sistem harus memungkinkan player menyerang menggunakan serangan jarak dekat.

### FR-06 — Ranged Attack

Sistem harus memungkinkan player melakukan serangan jarak jauh menggunakan projectile.

### FR-07 — Damage

Sistem harus mengurangi HP target ketika terkena serangan.

### FR-08 — Collision

Sistem harus mendeteksi collision antara:

```text
Melee Hitbox ↔ Enemy
Projectile ↔ Enemy
Player ↔ Ground
Enemy ↔ Ground
```

### FR-09 — Enemy AI

Sistem harus menyediakan computer-controlled opponent.

### FR-10 — Victory

Sistem harus menampilkan victory ketika HP enemy mencapai 0.

### FR-11 — Defeat

Sistem harus menampilkan defeat ketika HP player mencapai 0.

### FR-12 — Restart

Sistem harus memungkinkan permainan dimulai kembali.

### FR-13 — Pause

Sistem harus memungkinkan player melakukan pause.

### FR-14 — Character Replacement

Sistem harus memungkinkan mockup character diganti dengan sprite character sebenarnya.

---

# 17. Class Architecture

Struktur object-oriented yang disarankan:

```text
Game
 │
 ├── Menu
 │
 ├── Player
 │    ├── Movement
 │    ├── Attack
 │    ├── Health
 │    └── Animation
 │
 ├── Enemy
 │    ├── AI
 │    ├── Attack
 │    ├── Health
 │    └── Animation
 │
 ├── Projectile
 │
 ├── Arena
 │
 └── UI
      ├── HealthBar
      ├── Menu
      └── Text
```

---

# 18. Struktur Folder

```text
PyFight/
│
├── main.py
├── settings.py
├── game.py
│
├── player.py
├── enemy.py
├── projectile.py
│
├── combat.py
├── ai.py
│
├── menu.py
├── ui.py
│
├── assets/
│   ├── characters/
│   │   ├── player/
│   │   └── enemy/
│   │
│   ├── backgrounds/
│   ├── effects/
│   ├── sounds/
│   └── music/
│
└── README.md
```

---

# 19. State Management

Game menggunakan game state:

```text
MENU
  │
  ▼
PLAYING
  │
  ├──── PAUSED
  │
  ├──── VICTORY
  │
  └──── DEFEAT
```

Contoh:

```python
MENU = 0
PLAYING = 1
PAUSED = 2
VICTORY = 3
DEFEAT = 4
```

Kemudian:

```python
if game_state == MENU:
    show_menu()

elif game_state == PLAYING:
    play_game()

elif game_state == PAUSED:
    show_pause()

elif game_state == VICTORY:
    show_victory()

elif game_state == DEFEAT:
    show_defeat()
```

---

# 20. MVP — Versi Pertama

## Phase 1 — Basic Engine

- Window Pygame
- FPS
- Background
- Ground
- Player mockup
- Enemy mockup

## Phase 2 — Movement

- Left
- Right
- Jump
- Gravity
- Boundary

## Phase 3 — Combat

- Melee
- Hitbox
- Damage
- HP
- Ranged attack
- Projectile

## Phase 4 — AI

- Enemy movement
- Distance detection
- Melee AI
- Ranged AI

## Phase 5 — UI

- Main menu
- Health bar
- Pause
- Victory
- Defeat
- How to Play

## Phase 6 — Polish

- Sprite karakter
- Animation
- Sound effect
- Music
- Hit effect
- Screen shake
- Background
- Combo system

---

# 21. Future Development

## Character System

```text
Character Select
       │
 ┌─────┼─────┐
 ▼     ▼     ▼
Char A Char B Char C
```

Setiap karakter dapat memiliki:

- HP berbeda
- Speed berbeda
- Damage berbeda
- Melee berbeda
- Projectile berbeda
- Special ability

## Combo

Contoh:

```text
J → J → K
```

menghasilkan:

```text
COMBO x3
```

## Special Attack

Contoh:

```text
↓ → J
```

menghasilkan special attack.

## Difficulty

```text
EASY
NORMAL
HARD
```

## Character Selection

```text
┌──────────────────────────────────────┐
│          SELECT YOUR FIGHTER         │
│                                      │
│    [CHAR A]    [CHAR B]    [CHAR C] │
│                                      │
│              [ FIGHT ]               │
└──────────────────────────────────────┘
```

---

# 22. Acceptance Criteria MVP

Prototype dianggap berhasil apabila:

- [ ] Game dapat dijalankan dengan `python main.py`
- [ ] Main menu muncul.
- [ ] Player dapat memulai game.
- [ ] Player dapat bergerak.
- [ ] Player dapat melompat.
- [ ] Enemy dapat bergerak.
- [ ] Player dapat melakukan melee attack.
- [ ] Player dapat melakukan ranged attack.
- [ ] Projectile dapat mengenai enemy.
- [ ] HP berkurang ketika terkena serangan.
- [ ] Enemy memiliki AI.
- [ ] Enemy dapat menyerang player.
- [ ] Player dapat menang.
- [ ] Player dapat kalah.
- [ ] Victory screen muncul.
- [ ] Defeat screen muncul.
- [ ] Game dapat restart.
- [ ] Game dapat kembali ke main menu.
- [ ] Mockup character dapat diganti dengan sprite baru.

---

# 23. Target Prototype

Target awal adalah menghasilkan vertical slice yang dapat dimainkan:

```text
Main Menu
    ↓
Play
    ↓
Arena
    ↓
Player vs AI
    ↓
Melee + Projectile
    ↓
HP System
    ↓
Win / Lose
    ↓
Play Again / Main Menu
```

Setelah gameplay loop stabil, karakter asli, sprite, animasi, efek suara, combo, special attack, dan fitur tambahan dapat dikembangkan.
