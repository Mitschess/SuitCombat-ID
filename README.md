
# PyFight — 2D Retro Fighting Game (Player vs Computer)

PyFight adalah prototype game pertarungan 2D 1v1 antara Pemain (Player) dan Komputer (Computer AI) yang dibangun menggunakan Python dan Pygame.

---

## 🎮 Kontrol Permainan

### Pergerakan (Movement)

| Tombol      | Aksi                        |
| :---------- | :-------------------------- |
| **A** | Bergerak Kiri (Move Left)   |
| **D** | Bergerak Kanan (Move Right) |
| **W** | Melompat (Jump)             |
| **S** | Menunduk (Crouch Stance)    |

### Pertarungan (Combat)

| Tombol      | Aksi                                                 |
| :---------- | :--------------------------------------------------- |
| **J** | Serangan Jarak Dekat (Melee Attack)                  |
| **K** | Serangan Jarak Jauh (Ranged Energy Projectile)       |
| **L** | Bertahan / Tangkisan (Block - Mengurangi 75% Damage) |
| **U** | ULTI (saat meter ULTI penuh — tidak bisa ditangkis, harus dihindari) |

### Sistem & Navigasi

| Tombol                   | Aksi                         |
| :----------------------- | :--------------------------- |
| **ESC**            | Pause Game / Kembali ke Menu |
| **ENTER / SPACE**  | Memilih Menu / Play Again    |
| **ARROWS (↑/↓)** | Navigasi Menu                |

---

## 🥊 Karakter & ULTI

Pilih salah satu dari 5 karakter di layar **SELECT YOUR FIGHTER** (A/D atau panah, ENTER). CPU memakai karakter acak lainnya.

| Karakter | ULTI | Cara menghindar |
| :------- | :--- | :-------------- |
| **Gian** | Hujan Gian — 10 klon Gian jatuh di sekitar lawan | geser kiri/kanan |
| **Mega** | Banteng Ngamuk — banteng lari dari sisi Mega ke arah lawan | loncat |
| **Puba** | Petir Saham — 3 petir dari awan grafik saham | geser kiri/kanan |
| **Subi** | Misil Sawit — misil sawit melengkung (parabola) ke lawan | geser kiri/kanan |
| **Wowi** | Gedung Jatuh — gedung dijatuhkan dari atas | geser kiri/kanan |

Meter ULTI terisi saat memberi/menerima damage. Tanda merah di lantai menunjukkan titik jatuhnya serangan.

Suara khas karakter: taruh file `.wav` di `assets/characters/<Nama>/sounds/` (lihat `README.txt` di folder itu).
Aset dibuat ulang dengan `python generate_sprites.py` lalu `python generate_ulti.py`.

---

## 🚀 Cara Menjalankan Game

1. Pastikan **Python 3.x** dan **Pygame** sudah terinstall:

   ```bash
   pip install pygame
   ```
2. Jalankan game melalui terminal:

   ```bash
   python main.py
   ```

---

## 📂 Struktur Proyek

```text
FP-LBE-GIGA/
├── main.py              # Entry point utama game
├── settings.py          # Konfigurasi konstanta, warna, dimensi, & state game
├── game.py              # Core game loop engine & state manager
├── player.py            # Logika pergerakan & combat Player 1
├── enemy.py             # Logika pergerakan & combat Computer
├── ai.py                # Decision tree AI Computer (Distance-based logic)
├── combat.py            # Hitbox collision, damage calculation, & spark FX
├── projectile.py        # Proyektil energi & particle trails
├── menu.py              # Main Menu & How To Play interface
├── ui.py                # Health bar, floating damage text, & overlays
├── sound_generator.py   # Generator audio 8-bit retro WAV
├── assets/              # Direktori aset gambar & suara
│   ├── characters/
│   │   ├── player/
│   │   └── enemy/
│   ├── backgrounds/
│   ├── effects/
│   ├── sounds/
│   └── music/
└── README.md
```

---

## 🎯 Fitur & Kepatuhan PRD/SRS

- ✅ **Main Menu & Navigasi** (`PLAY`, `HOW TO PLAY`, `QUIT`) dengan dukungan Keyboard & Mouse.
- ✅ **Movement & Physics** (Move, Jump, Crouch, Boundaries, Gravity).
- ✅ **Sistem Pertarungan Dual-Mode** (Melee Punch/Slash & Ranged Energy Projectile).
- ✅ **Tangkisan & Defend System** (`L` key mengurangi damage sebesar 75%).
- ✅ **Computer AI State Machine** (Responsif berdasarkan jarak lawan: approach, ranged attack, melee, reactive blocking).
- ✅ **Health & Damage System** (Interpolasi bar HP mulus, damage indicators floating text, hit flash).
- ✅ **Juice & Polish** (Screen shake pada serangan berat, particle sparks, audio retro WAV synth).
- ✅ **Dukungan Penggantian Sprite** (Mendukung rendering mockup dan sprite PNG otomatis).
