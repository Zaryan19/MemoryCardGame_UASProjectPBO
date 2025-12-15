import tkinter as tk
from tkinter import ttk, messagebox
import random
import time

# --- PENGATURAN TAMPILAN DASAR ---
CARD_FONT = ('Arial', 16, 'bold') # Font untuk teks pada kartu
CARD_PADDING = [15, 15] # Padding (ruang) di dalam tombol kartu

# --- A. KELAS KONFIGURASI LEVEL ---
class GameConfig:
    """Kelas Induk (Polymorphic) untuk menyimpan konfigurasi ukuran papan."""
    def __init__(self, name, rows, cols):
        self.name = name # Nama level (e.g., "Level 1 (4x4)")
        self.rows = rows # Jumlah baris grid
        self.cols = cols # Jumlah kolom grid
        self.total_cards = rows * cols # Total kartu di papan
        
    def generate_card_values(self):
        """Menghasilkan list nilai kartu (misal ['A', 'A', 'B', 'B', ...]) yang sudah dikocok."""
        num_pairs = self.total_cards // 2
        
        if self.total_cards % 2 != 0:
            raise ValueError(f"Level {self.name} memiliki jumlah kartu ganjil ({self.total_cards}). Permainan pasangan harus genap.")
            
        if num_pairs > 26:
            raise ValueError("Grid terlalu besar, melebihi 26 pasangan.")
            
        values = [chr(65 + i) for i in range(num_pairs)]
        cards = values * 2
        random.shuffle(cards)
        return cards

class EasyConfig(GameConfig):
    """Konfigurasi untuk Level 1 (4x4)."""
    def __init__(self):
        super().__init__("Level 1 (4x4)", 4, 4)

class MediumConfig(GameConfig):
    """Konfigurasi untuk Level 2 (4x6)."""
    def __init__(self):
        super().__init__("Level 2 (4x6)", 4, 6)

class HardConfig(GameConfig):
    """Konfigurasi untuk Level 3 (6x6)."""
    def __init__(self):
        super().__init__("Level 3 (6x6)", 6, 6)


# --- B. KELAS TOMBOL KARTU ---
class CardButton(ttk.Button):
    """Kelas dasar untuk tombol kartu."""
    def __init__(self, master, card_value, index, **kwargs):
        super().__init__(master, **kwargs)
        self.card_value = card_value # Nilai kartu yang tersembunyi (misal 'A')
        self.index = index # Indeks posisi kartu di list data
        self.is_matched = False # Status kecocokan kartu
        
    def reset_visual(self):
        """Menyembunyikan nilai kartu dan mengembalikan ke state normal (tertutup)."""
        self.config(text=" ", state=tk.NORMAL, style='Card.TButton')
        
    def show_value(self):
        """Menampilkan nilai kartu saat dibalik."""
        self.config(text=self.card_value, style='Opened.TButton')
    
    def apply_match_style(self):
        """Menerapkan style dasar saat kartu cocok (Metode Induk)."""
        self.is_matched = True
        self.config(style='Matched.TButton', state=tk.DISABLED)

    def show_temporarily(self):
        """Menampilkan nilai untuk fitur hint."""
        self.config(text=self.card_value, style='Hint.TButton', state=tk.DISABLED)
    
    def hide_temporarily(self):
        """Menyembunyikan kartu setelah hint selesai."""
        if not self.is_matched:
            self.reset_visual()
            self.config(state=tk.NORMAL)
        else:
            self.apply_match_style()
        
class MatchableCardButton(CardButton):
    """Kelas Kartu yang menerapkan styling unik saat cocok (Method Overriding)."""
    def apply_match_style(self):
        """Menimpa metode induk untuk menambahkan style foreground kustom."""
        super().apply_match_style() 
        self.config(style='CustomMatchText.TButton') 


# --- C. KELAS GAME LOGIC DAN TAMPILAN (FRAME) ---
class MemoryGame(tk.Frame): 
    """Frame utama yang berisi logika permainan dan tata letak grid."""
    def __init__(self, master, app, initial_config): 
        super().__init__(master, bg='white') 
        self.app = app # Referensi ke root window (AplikasiUtama)
        
        self.style = ttk.Style() # Style TTK untuk widget
        
        self.config = initial_config # Konfigurasi level yang dipilih
        self.timer_id = None # ID untuk mengontrol fungsi after() timer
        
        self.reset_game_state()
        
        self.create_widgets()
        self.start_game()

    def reset_game_state(self):
        """Mempersiapkan ulang semua variabel status untuk permainan baru."""
        self.current_cards = self.config.generate_card_values() # List nilai kartu yang dikocok
        self.buttons = [] # List 2D objek tombol kartu
        self.opened_cards = [] # List 1-2 kartu yang sedang terbuka saat ini
        self.matched_indices = [] # Indeks kartu yang sudah cocok
        self.move_count = 0 # Jumlah langkah (pasangan balik)
        self.can_click = True # Bendera kontrol klik kartu
        self.is_paused = False # Status jeda permainan
        self.hint_count = 2 # Jumlah hint yang tersedia
        self.hint_in_progress = False # Status hint sedang berjalan

    def reset_game(self):
        """Menghentikan timer dan kembali ke halaman pemilihan level."""
        if self.timer_id:
            self.app.after_cancel(self.timer_id) 
            
        self.app.show_frame(LevelSelection) 

    def start_game(self):
        """Memulai timer permainan."""
        self.start_time = time.time()
        self.update_timer()

    def create_widgets(self):
        """Membuat dan menata semua elemen UI game (grid kartu, label info, kontrol)."""
        for widget in self.winfo_children():
            widget.destroy()
            
        board_frame = tk.Frame(self, bg='white')
        board_frame.pack(pady=10)
        
        self.buttons = []
        for row in range(self.config.rows):
            button_row = []
            for col in range(self.config.cols):
                card_index = row * self.config.cols + col
                card_value = self.current_cards[card_index]
                
                button = MatchableCardButton(
                    board_frame, 
                    card_value=card_value, 
                    index=card_index,
                    style='Card.TButton',
                    command=lambda r=row, c=col: self.handle_click(r, c)
                )
                
                button.grid(row=row, column=col, padx=5, pady=5)
                button_row.append(button)
            self.buttons.append(button_row)
        
        # Label Info Level dan Langkah
        self.level_label = tk.Label(
            self, 
            text=f"{self.config.name} | Langkah: {self.move_count}", 
            font=('Arial', 12, 'italic'),
            bg='white'
        )
        self.level_label.pack()

        info_frame = tk.Frame(self, bg='white')
        info_frame.pack(pady=(5, 0))

        # Label Timer
        self.timer_label = tk.Label(info_frame, text="Waktu: 0s", font=('Arial', 12), bg='white')
        self.timer_label.pack(side=tk.LEFT, padx=10)
        
        # Label Status Game (Pencocokan, Jeda)
        self.status_label = tk.Label(self, text="Temukan semua pasangan!", font=('Arial', 12), bg='white')
        self.status_label.pack(pady=(5, 5))
        
        control_frame = tk.Frame(self, bg='white')
        control_frame.pack(pady=(5, 5))

        # Tombol Jeda/Lanjut
        self.pause_button = ttk.Button(control_frame, text="⏸ Jeda", command=self.toggle_pause, style='Accent.TButton')
        self.pause_button.pack(side=tk.LEFT, padx=5)

        # Tombol Hint
        self.hint_button = ttk.Button(
            control_frame, 
            text=f"💡 Hint ({self.hint_count})", 
            command=self.show_hint, 
            style='Accent.TButton',
            state=tk.NORMAL if self.hint_count > 0 else tk.DISABLED
        )
        self.hint_button.pack(side=tk.LEFT, padx=5)
        
        # Tombol Reset
        ttk.Button(self, text="🔄 Reset Game", command=self.reset_game, style='Reset.TButton').pack(pady=(10, 15))


    def update_timer(self):
        """Memperbarui waktu yang telah berlalu setiap detik."""
        if not self.is_paused:
            elapsed_time = int(time.time() - self.start_time)
            self.timer_label.config(text=f"Waktu: {elapsed_time}s")
        self.timer_id = self.app.after(1000, self.update_timer) 

    def toggle_pause(self):
        """Mengatur status jeda (pause) dan memperbarui UI terkait."""
        if self.is_paused:
            self.is_paused = False
            self.pause_button.config(text="⏸ Jeda", style='Accent.TButton')
            
            # Kembali ke status dan warna normal
            self.level_label.config(text=f"{self.config.name} | Langkah: {self.move_count}", fg='black')
            self.status_label.config(text="Lanjutkan permainan!", fg='black') 
            
            self.can_click = True
            self.unlock_all_cards()
            if self.hint_count > 0 and not self.hint_in_progress:
                self.hint_button.config(state=tk.NORMAL)
        else:
            self.is_paused = True
            self.pause_button.config(text="▶ Lanjut", style='Reset.TButton')
            
            # Mengatur tampilan jeda
            self.level_label.config(text=f"{self.config.name} | Langkah: {self.move_count}", fg='gray')
            self.status_label.config(text="⏸ Permainan Dijeda ⏸", fg='blue')
            
            self.can_click = False
            self.lock_all_cards()
            self.hint_button.config(state=tk.DISABLED)

    def show_hint(self):
        """Mengaktifkan fitur hint (menampilkan kartu sebentar)."""
        if self.hint_count <= 0 or self.is_paused or self.hint_in_progress:
            return

        self.hint_in_progress = True
        self.can_click = False
        self.lock_all_cards()
        self.hint_button.config(state=tk.DISABLED)

        for row in self.buttons:
            for button in row:
                if not button.is_matched:
                    button.show_temporarily()
        
        self.status_label.config(text="🤫 HINT! Lihat baik-baik...", fg='blue')
        self.hint_count -= 1
        self.hint_button.config(text=f"💡 Hint ({self.hint_count})")

        self.app.after(2000, self.hide_hint) 

    def hide_hint(self):
        """Menyembunyikan kartu setelah periode hint selesai."""
        for row in self.buttons:
            for button in row:
                button.hide_temporarily()
                
        self.status_label.config(text="Temukan semua pasangan!", fg='black')
        self.can_click = True
        self.hint_in_progress = False
        self.unlock_all_cards()
        if self.hint_count > 0:
            self.hint_button.config(state=tk.NORMAL)

    def lock_all_cards(self):
        """Menonaktifkan (disable) semua kartu yang belum cocok."""
        for row in self.buttons:
            for button in row:
                if not button.is_matched and button.cget('state') == tk.NORMAL:
                    button.config(state=tk.DISABLED)

    def unlock_all_cards(self):
        """Mengaktifkan (enable) semua kartu yang belum cocok."""
        for row in self.buttons:
            for button in row:
                if not button.is_matched:
                    button.config(state=tk.NORMAL)

    def handle_click(self, row, col):
        """Menangani logika saat pemain mengklik sebuah kartu."""
        if not self.can_click or self.is_paused:
            return

        button = self.buttons[row][col] 

        if button in self.opened_cards or button.is_matched:
            return

        button.show_value() 
        button.config(state=tk.DISABLED)
        self.opened_cards.append(button)

        if len(self.opened_cards) == 2:
            self.can_click = False 
            self.lock_all_cards()
            self.move_count += 1
            self.level_label.config(text=f"{self.config.name} | Langkah: {self.move_count}")
            
            self.app.after(1000, self.handle_check_match) 

    def handle_check_match(self):
        """Mengecek apakah dua kartu yang terbuka cocok atau tidak."""
        if len(self.opened_cards) < 2:
            self.unlock_all_cards()
            self.can_click = True
            return

        card1 = self.opened_cards[0]
        card2 = self.opened_cards[1]
        
        if card1.card_value == card2.card_value:
            self.status_label.config(text="🎉 Cocok!", fg='green')
            
            card1.apply_match_style() # Delegasi styling ke objek kartu
            card2.apply_match_style()
            
            self.matched_indices.append(card1.index)
            self.matched_indices.append(card2.index)

        else:
            self.status_label.config(text="❌ Tidak Cocok. Coba lagi.", fg='red')
            
            for button in self.opened_cards:
                button.reset_visual() # Menyembunyikan kartu
                
        self.opened_cards = []
        self.can_click = True
        self.unlock_all_cards()

        if len(self.matched_indices) == len(self.current_cards):
            self.status_label.config(text="Semua pasangan ditemukan!", fg='purple')
            elapsed_time = int(time.time() - self.start_time)
            
            if self.timer_id:
                self.app.after_cancel(self.timer_id) 
                
            messagebox.showinfo(
                "Selamat!", 
                f"Anda menang dalam {self.move_count} langkah dan {elapsed_time} detik di {self.config.name}!"
            )
            self.app.after(500, lambda: self.app.show_frame(LevelSelection))


# --- E. KELAS MAIN MENU ---
class MainMenu(tk.Frame):
    """Frame yang menampilkan tombol Play dan Quit."""
    def __init__(self, master, app): 
        super().__init__(master, bg='white')
        self.app = app # Referensi ke AplikasiUtama
        
        tk.Label(self, text="🎮 MEMORY CARD GAME 🧠", font=('Arial', 24, 'bold'), bg='white').pack(pady=40)
        
        ttk.Button(
            self, 
            text="▶ PLAY", 
            command=lambda: self.app.show_frame(LevelSelection), 
            style='Menu.TButton'
        ).pack(pady=15, ipadx=20)
        
        ttk.Button(
            self, 
            text="❌ QUIT", 
            command=self.app.quit, 
            style='Reset.TButton'
        ).pack(pady=15, ipadx=20)

# --- F. KELAS PEMILIHAN LEVEL ---
class LevelSelection(tk.Frame):
    """Frame yang menampilkan pilihan level (Level 1, 2, 3)."""
    def __init__(self, master, app): 
        super().__init__(master, bg='white')
        self.app = app 
        
        tk.Label(self, text="PILIH LEVEL KESULITAN", font=('Arial', 20, 'bold'), bg='white').pack(pady=30)
        
        levels = [EasyConfig(), MediumConfig(), HardConfig()]
        
        for level in levels:
            ttk.Button(
                self, 
                text=level.name, 
                command=lambda l=level: self.app.start_game(l), 
                style='Menu.TButton'
            ).pack(pady=10, ipadx=10, fill='x', padx=50)

        ttk.Button(
            self, 
            text="◀ BACK", 
            command=lambda: self.app.show_frame(MainMenu), 
            style='Reset.TButton'
        ).pack(pady=20, ipadx=20)

# --- D. KELAS UTAMA TKINTER (ROOT WINDOW) ---
class AplikasiUtama(tk.Tk):
    """Kelas root window utama yang mengatur style dan navigasi antar frame."""
    def __init__(self):
        super().__init__()
        self.title("🎮 Memory Card Game (OOP Tkinter)")
        self.configure(bg='white')
        
        # Mendaftarkan style TTK agar tersedia di semua frame sejak awal
        self.define_styles()
        
        # Frame Container: Menampung semua frame (MainMenu, LevelSelection, MemoryGame)
        self.container = tk.Frame(self, bg='white')
        self.container.pack(side="top", fill="both", expand=True)
        
        self.frames = {} # Dictionary untuk menyimpan referensi frame
        
        # Inisialisasi MainMenu dan LevelSelection
        for F in (MainMenu, LevelSelection):
            frame = F(self.container, self) 
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew") # Menggunakan grid untuk layering
        
        self.show_frame(MainMenu) # Tampilkan Main Menu saat pertama kali dibuka
        
        self.resizable(False, False) # Menonaktifkan resizing window

    def define_styles(self): 
        """Mendefinisikan style visual untuk widget TTK."""
        style = ttk.Style()
        style.theme_use('clam')

        # Definisi Warna Kartu
        bg_card = '#4CAF50'
        fg_card = 'white'
        bg_opened = '#4CAF50'
        fg_opened = '#FFFF00'
        bg_matched = '#FFD700'
        fg_matched = '#B8860B'
        bg_hint = '#2196F3'
        fg_hint = 'white'

        # Konfigurasi Styles Kartu
        style.configure('Card.TButton', font=CARD_FONT, background=bg_card, foreground=fg_card, relief='raised', padding=CARD_PADDING)
        style.configure('Opened.TButton', font=CARD_FONT, background=bg_opened, foreground=fg_opened, relief='raised', padding=CARD_PADDING)
        style.configure('Matched.TButton', font=CARD_FONT, background=bg_matched, relief='sunken', padding=CARD_PADDING)
        style.configure('CustomMatchText.TButton', 
                             font=CARD_FONT, 
                             background=bg_matched, 
                             foreground=fg_matched, 
                             relief='sunken', 
                             padding=CARD_PADDING) 
        style.configure('Hint.TButton', font=CARD_FONT, background=bg_hint, foreground=fg_hint, relief='raised', padding=CARD_PADDING)
        
        # Styles Menu dan Kontrol
        style.configure('Accent.TButton', font=('Arial', 12, 'bold'), background='#2196F3', foreground='white')
        style.configure('Reset.TButton', font=('Arial', 12, 'bold'), background='#FF9800', foreground='white')
        style.configure('Menu.TButton', font=('Arial', 16, 'bold'), background='#2196F3', foreground='white')


    def show_frame(self, cont):
        """Menampilkan frame tertentu (halaman) di atas container."""
        frame = self.frames[cont]
        frame.tkraise()
        self.config(menu=tk.Menu(self)) 

    def start_game(self, config):
        """Membuat instance MemoryGame baru dan memindahkannya ke tampilan game."""
        
        # Hapus frame game lama jika ada
        if MemoryGame in self.frames:
            self.frames[MemoryGame].destroy()
            del self.frames[MemoryGame]
            
        # Buat frame game baru dengan konfigurasi level yang dipilih
        game_frame = MemoryGame(self.container, self, initial_config=config)
        self.frames[MemoryGame] = game_frame
        game_frame.grid(row=0, column=0, sticky="nsew")
        game_frame.tkraise()


# --- EKSEKUSI PROGRAM UTAMA ---
if __name__ == "__main__":
    app = AplikasiUtama()
    app.mainloop()