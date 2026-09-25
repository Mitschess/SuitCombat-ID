
# Suit Combat ID — 2D Retro Fighting Game

Suit Combat ID adalah game pertarungan 2D 1v1 antara Pemain (Player) dan Komputer (Computer AI) yang dibangun menggunakan Python dan Pygame.

---
<img width="1280" height="717" alt="image" src="https://github.com/user-attachments/assets/c0f665a1-a645-4b03-a134-23b649f30fa5" />
<img width="1281" height="718" alt="image" src="https://github.com/user-attachments/assets/e1dd6919-65fc-44a7-8f82-01b28777154d" />
<img width="1282" height="720" alt="image" src="https://github.com/user-attachments/assets/918a9174-e63e-4b69-bba5-7ed1861679fe" />
<img width="1280" height="718" alt="image" src="https://github.com/user-attachments/assets/93cb70f1-b39b-4de7-a050-4e46ed3d61bb" />
<img width="1277" height="717" alt="image" src="https://github.com/user-attachments/assets/4a6f6855-2aa6-4136-aa7c-c376faf220a0" />


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
| **F11**            | Fullscreen on/off |
| **ENTER / SPACE**  | Memilih Menu / Play Again    |
| **ARROWS (↑/↓)** | Navigasi Menu                |

---

## 🥊 Karakter & ULTI

Di layar **PILIH JAGOAN** pilih karaktermu (A/D atau panah, ENTER), lalu di **PILIH LAWAN** pilih karakter CPU atau kartu **ACAK** untuk lawan acak (ESC untuk mengganti jagoan).

| Karakter | ULTI | Cara menghindar |
| :------- | :--- | :-------------- |
| **Gian** | Hujan Gian — 10 klon Gian jatuh di sekitar lawan | geser kiri/kanan |
| **Mega** | Banteng Ngamuk — banteng lari dari sisi Mega ke arah lawan | loncat |
| **Puba** | Petir Saham — 3 petir dari awan grafik saham | geser kiri/kanan |
| **Subi** | Misil Sawit — misil sawit melengkung (parabola) ke lawan | geser kiri/kanan |
| **Wowi** | Gedung Jatuh — gedung dijatuhkan dari atas | geser kiri/kanan |

Setelah memilih karakter, pilih **ARENA** (IKN, Istana, Kopdes, Dapur MBG, Kebun Sawit, Arena Kuil) dan **DIFFICULTY**:

| Difficulty | CPU |
| :--------- | :-- |
| **EASY**   | lambat, jarang menyerang & menangkis, jarang menghindari ULTI |
| **MEDIUM** | seimbang |
| **HARD**   | cepat, damage lebih besar, sering menangkis, hampir selalu menghindari ULTI |

**Health (nampan MBG):** setiap 8–13 detik sebuah nampan jatuh di posisi acak. Siapa pun yang menyentuhnya duluan (pemain atau CPU) mendapat **+1/3 nyawa (33 HP)**. Nampan menghilang (berkedip dulu) kalau tidak diambil. CPU yang HP-nya rendah akan mengejar nampan — makin tinggi difficulty, makin sering.

Meter ULTI terisi saat memberi/menerima damage. Tanda merah di lantai menunjukkan titik jatuhnya serangan.

Suara khas karakter: taruh file `.wav` di `assets/characters/<Nama>/sounds/` (lihat `README.txt` di folder itu).
Menu **SETTINGS** (dari menu utama atau pause): volume master / musik / efek suara dan fullscreen — tersimpan di `config.json`.

Musik & efek suara dibuat oleh `python generate_audio.py`; sprite health oleh `python generate_pickups.py`. Aset dibuat ulang dengan `python generate_sprites.py`, `python generate_ulti.py`, lalu `python generate_stages.py` (latar dari `assets/latar_*.jpg`).

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
