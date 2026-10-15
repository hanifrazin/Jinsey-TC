# Jinsey — Jinja to Test Cases using Python

Tool lokal untuk menulis test case di Jinja2, kemudian menghasilkan YAML dan Excel.
Contoh aplikasi **Lentera** sepenuhnya fiktif: 5 Login, 3 Register, dan 2 Logout.
Seluruh alamat contoh menggunakan domain `example.test`. Tidak ada data pekerjaan terdahulu.
Jinsey adalah alat authoring/export; tidak menjalankan skenario aplikasi.

**Baru mulai? Baca [Panduan Jinja untuk pemula](docs/panduan-jinja.md).**
Panduan tersebut menjelaskan struktur file, arti setiap field, perbedaan versi
lengkap dan clean, cara memakai `active_account()`, serta contoh menambah TC.

## Setup Windows, Linux, dan macOS

Jinsey memerlukan **Python 3.12+** dan **uv**. uv dapat memasang Python sekaligus
dependency project, sehingga kamu tidak perlu memasang package Python satu per satu.
File lock memakai `filelock` dengan backend sesuai OS, bukan import `fcntl` langsung.
Pengujian lokal pada pembaruan ini dilakukan di macOS; Windows dan Linux belum
dijalankan langsung dalam sesi ini.

### 1. Install uv sesuai OS

Pilih satu cara sesuai OS. Perintah berikut mengikuti
[dokumentasi instalasi resmi uv](https://docs.astral.sh/uv/getting-started/installation/).

**Windows — buka PowerShell:**

```powershell
winget install --id=astral-sh.uv -e
```

Jika WinGet tidak tersedia, installer PowerShell resmi juga dapat dipakai:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux — buka Terminal:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Jika `curl` tidak tersedia, gunakan alternatif installer resmi:

```bash
wget -qO- https://astral.sh/uv/install.sh | sh
```

**macOS — buka Terminal:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Jika sudah menggunakan Homebrew, kamu dapat memilih `brew install uv` sebagai gantinya.
Setelah instalasi, tutup dan buka lagi terminal atau terminal editor, lalu periksa:

```text
uv --version
```

### 2. Buka folder project dan install dependency

Unduh/extract project atau clone repository jika tersedia. Jika memakai Git,
Git hanya diperlukan untuk clone/update; menjalankan Jinsey tidak membutuhkan Git.
Buka folder yang berisi `pyproject.toml`, `uv.lock`, `config/`, dan `data/`.

Contoh pindah folder di **Windows PowerShell** (ganti path sesuai lokasi project):

```powershell
cd "C:\Users\NamaKamu\Documents\Jinsey-TC"
```

Contoh di **Linux/macOS**:

```bash
cd "$HOME/Documents/Jinsey-TC"
```

Perintah selanjutnya sama pada ketiga OS:

```text
uv python install 3.12
uv sync --locked --python 3.12
uv run python --version
```

`uv python install 3.12` menyiapkan interpreter Python; langkah ini berguna ketika
Python yang sesuai belum terpasang. Lihat [panduan Python resmi uv](https://docs.astral.sh/uv/guides/install-python/).
`uv sync` membuat `.venv/` lokal dan memasang versi dependency dari `uv.lock`,
termasuk CLI `jinsey`. Jalankan ulang `uv sync --locked` setelah menerima perubahan
dependency project. Koneksi internet diperlukan saat unduhan pertama.

Tidak perlu menjalankan `pip install jinja2`, memasang Jinsey secara global,
atau mengaktifkan `.venv` manual. `uv run` memilih environment project secara otomatis.
Jika berpindah OS, jalankan setup pada salinan project di OS tersebut; buat `.venv`
melalui `uv sync`, jangan menyalin virtual environment dari komputer sebelumnya.

### Package dan plugin yang diperlukan

| Komponen | Kegunaan | Cara memasang |
| --- | --- | --- |
| Python 3.12+ | Menjalankan kode Jinsey | `uv python install 3.12` |
| uv | Mengelola environment, package, dan perintah CLI | Installer sesuai OS di atas |
| Jinja2 | Membaca template `.j2` | Otomatis melalui `uv sync --locked` |
| PyYAML | Validasi konfigurasi dan export YAML | Otomatis melalui `uv sync --locked` |
| openpyxl | Membuat dan memeriksa Excel | Otomatis melalui `uv sync --locked` |
| filelock | Mengunci registry ID lintas proses/OS | Otomatis melalui `uv sync --locked` |
| pytest dan pytest-cov | Unit test dan laporan coverage | Otomatis melalui `uv sync --locked` (dependency development) |
| Ruff, Bandit, pip-audit | Lint, pemeriksaan kode keamanan, dan audit advisory dependency | Otomatis melalui `uv sync --locked` (dependency development) |

**Tidak ada plugin editor yang wajib dipasang untuk menjalankan Jinsey.**
Kamu bisa mengedit `.j2` memakai editor teks. Extension Jinja/Python pada editor
bersifat opsional untuk syntax highlighting, navigasi, atau folding. Dukungan
Sticky Scroll bergantung editor dan extension, bukan syarat menjalankan generator.
`SKILL.md` adalah panduan untuk coding agent, bukan package atau plugin runtime.
Microsoft Excel juga tidak perlu terpasang untuk menghasilkan `.xlsx`; gunakan
aplikasi spreadsheet jika ingin membuka hasil dan mencoba dropdown secara interaktif.

### 3. Validasi dan generate

Jalankan dari root project pada ketiga OS. Perintah satu baris berikut bisa dipakai
di PowerShell Windows maupun shell Linux/macOS:

```bash
uv run jinsey validate --template testcases.j2
uv run jinsey generate --template testcases.j2 --format all
uv run jinsey validate --template testcases_clean.j2
uv run jinsey generate --template testcases_clean.j2 --format all
```

Sumber dan tujuan yang digunakan:

| Template | Folder hasil |
| --- | --- |
| `data/input/testcases.j2` | `data/output/testcases/` |
| `data/input/testcases_clean.j2` | `data/output/testcases_clean/` |

Masing-masing folder berisi `testcases.yaml` dan `testcases.xlsx`.
Perintah `uv run jinsey generate` tanpa `--template` memilih `testcases.j2`.

Opsi lain dan pengujian:

```bash
uv run jinsey generate --format yaml
uv run jinsey generate --format excel
uv run jinsey generate --prefix AUTH
uv run jinsey generate --dry-run
uv run pytest --cov=jinsey --cov-report=term-missing
```

Tidak perlu mengaktifkan virtual environment. Dependency runtime dan development dikelola
di `pyproject.toml` dan dikunci di `uv.lock`.

### Jika setup atau generate gagal

| Gejala | Langkah berikutnya |
| --- | --- |
| `uv` tidak dikenali / `command not found` | Buka terminal baru setelah install; ikuti petunjuk PATH dari installer dan periksa `uv --version` |
| Python belum tersedia atau versinya terlalu lama | Jalankan `uv python install 3.12`, kemudian `uv sync --locked --python 3.12` |
| `jinsey` tidak ditemukan | Pastikan terminal berada di root project, jalankan `uv sync --locked`, lalu gunakan `uv run jinsey ...` |
| `Template not found` | Simpan file di `data/input/` dan gunakan nama file, atau berikan path eksplisit |
| Path mengandung spasi | Gunakan tanda kutip, misalnya `--template "data/input/login contoh.j2"` |
| `Permission denied` saat menulis Excel, terutama Windows | Tutup workbook hasil di Excel, lalu generate ulang; pastikan folder tujuan dapat ditulis |
| Unduhan dependency gagal | Periksa koneksi/proxy yang digunakan, kemudian ulangi `uv sync --locked` |

## Folder input dan output

```text
data/
├── input/
│   ├── testcases.j2
│   ├── testcases_clean.j2
│   └── shared/
│       ├── login_steps.j2
│       └── preconditions.j2
└── output/
    ├── testcases/
    │   ├── testcases.yaml
    │   └── testcases.xlsx
    └── testcases_clean/
        ├── testcases.yaml
        └── testcases.xlsx
```

`generate` default menghasilkan `data/output/testcases/testcases.yaml` dan
`data/output/testcases/testcases.xlsx`.
Tanpa `--template`, file yang dibaca adalah **`data/input/testcases.j2`**.
Untuk versi clean, gunakan `uv run jinsey generate --template testcases_clean.j2`.
Nama file saja dicari di `data/input/`. Path eksplisit, misalnya
`--template data/input/testcases_clean.j2`, `--template ./custom.j2`, atau path
absolut, juga didukung. Hasil otomatis masuk ke `data/output/<nama-file-tanpa-.j2>/`.
Contoh: `testcases_clean.j2` → `data/output/testcases_clean/`. CLI menampilkan
template yang dibaca agar sumber hasil selalu jelas. Nama file dengan stem yang
sama memakai tujuan default yang sama; tentukan `--output-dir` jika perlu dibedakan.
Hasil lama sebelum migrasi folder dipertahankan di `data/output/legacy/` jika tersedia.
Opsi `--output-dir`, `--fields`, `--registry` menerima path lain. Prefix default `TC`,
dapat ditentukan dalam envelope template atau masing-masing kasus. `--prefix`
menimpa seluruh prefix kasus dan file bila diberikan.
Prefix menerima huruf besar, angka, underscore, dimulai huruf, maksimum 32 karakter.
`--format yaml` / `excel` hanya menulis format pilihan; format lain yang sudah ada
tidak diperbarui. Gunakan `all` untuk memperbarui keduanya dalam satu transaksi.
`validate` memeriksa template dan schema tanpa membaca/menulis registry atau output.
`--dry-run` menampilkan rencana ID dan tidak membuat file maupun direktori.
Exit code `0` berarti sukses, `1` untuk kegagalan input/generasi, `2` untuk argumen CLI salah.

## Satu folder menjadi satu workbook dengan banyak sheet

Gunakan `--input-dir` untuk menggabungkan beberapa template menjadi satu Excel:

```text
data/input/auth_suite/
├── login_negative.j2
├── login_positive.j2
├── logout.j2
├── register_negative.j2
└── register_positive.j2
```

Contoh folder lima file di atas sudah tersedia dan berisi total 10 kasus fiktif.
Jalankan dari root project:

```bash
uv run jinsey validate --input-dir auth_suite
uv run jinsey generate --input-dir auth_suite --format excel
```

Hasil: **`data/output/auth_suite/testcases.xlsx`**, dengan lima sheet bernama
`login_negative`, `login_positive`, `logout`, `register_negative`, `register_positive`.
Satu file dapat berisi satu atau banyak TC; setiap TC tetap satu baris di sheet-nya.
Dropdown Priority, multiline cells, freeze header, dan filter berlaku di setiap sheet.
Tidak ada sheet ringkasan tambahan. Untuk opsi dropdown panjang, exporter tetap
dapat membuat satu sheet lookup tersembunyi `_choices`.

Untuk folder milikmu, misalnya `data/input/fitur_login/`, cukup gunakan
`uv run jinsey generate --input-dir fitur_login --format excel`.
Folder bertingkat juga dapat dipilih: `--input-dir modul/fitur_login` akan mencari
`data/input/modul/fitur_login` jika path relatif tersebut tidak ada dari root project.
Path eksplisit atau absolut tetap didukung. `--template auth_suite` juga menerima
folder, tetapi `--input-dir` lebih menjelaskan maksudnya; jangan gunakan kedua opsi sekaligus.

Aturan mode folder:

- Hanya file `.j2` langsung di folder pilihan yang dibaca, tanpa rekursi. File
  tersembunyi dan file selain `.j2` diabaikan. Urutan sheet mengikuti nama file
  secara alfabetis, tanpa membedakan huruf besar/kecil; gunakan `01_`, `02_` bila perlu.
- Setiap file tetap menghasilkan envelope `test_cases` melalui `tojson` seperti
  template tunggal. Taruh macro/include di subfolder `shared/` milik suite agar
  tidak dianggap input sheet. Import tetap dibatasi dalam direktori template.
- Nama sheet sama dengan nama file tanpa `.j2`. Nama harus 1–31 karakter, unik
  tanpa membedakan huruf besar/kecil, tanpa karakter `[]:*?/\\` atau apostrof di
  awal/akhir. Nama `_choices` dicadangkan. Nama yang tidak valid ditolak, bukan
  dipotong atau diubah diam-diam.
- `key` harus unik di seluruh folder, termasuk antar-prefix. Jangan menggabungkan
  versi clean dan lengkap dari kasus yang sama dalam satu suite karena key-nya sama.
- Counter prefix dibagi antarsheet. Dua file dengan prefix `LOGIN` meneruskan
  counter yang sama; prefix berbeda mempunyai counter terpisah. Prefix file hanya
  menjadi fallback bagi kasus dalam file itu. `--prefix AUTH` menimpa seluruh kasus.
- Registry yang sama mempertahankan ID walau file/sheet di-rename atau kasus
  dipindahkan ke file lain. Pertahankan `key` dan prefix untuk identitas yang sama.
- Semua file divalidasi sebelum output dan registry di-commit. Jika satu file
  gagal, seluruh generate gagal; output sebelumnya tetap dipertahankan.
- `--output-dir`, `--registry`, `--dry-run`, dan pilihan format tetap tersedia.

Untuk menghasilkan satu YAML dan satu Excel dalam transaksi yang sama:

```bash
uv run jinsey generate --input-dir auth_suite --format all
```

YAML mode folder menggunakan envelope `sheets` agar hubungan file/sheet tetap jelas.
Setiap item berisi `name`, `source`, dan `test_cases`. YAML mode satu file tetap
menggunakan envelope `test_cases` seperti sebelumnya.

## Authoring

Tersedia dua contoh template dengan 10 kasus yang sama:

- `data/input/testcases.j2`: versi lengkap untuk dibaca per TC. Semua prasyarat,
  langkah, expected result, priority, tags, test data, dan test type tertulis langsung
  dalam satu file, tanpa import, macro, atau loop. ID referensi ditampilkan dalam
  komentar; ID aktual tetap diberikan generator berdasarkan `key` dan registry.
- `data/input/testcases_clean.j2`: versi reusable dengan macro dari `data/input/shared/`
  dan loop untuk lima kasus Login. Template ini adalah versi clean sebelumnya.

Pilih salah satu untuk diedit; perubahan pada satu file tidak otomatis disalin ke
file lainnya. Jangan menggabungkan kedua template karena key kasusnya sama.
Keduanya memakai registry yang sama, sehingga berpindah template mempertahankan ID.

```bash
uv run jinsey generate --template testcases.j2
uv run jinsey generate --template testcases_clean.j2
```

Setiap template menghasilkan satu envelope JSON yang berisi banyak kasus.
Gunakan `namespace(cases=[])`, blok `set` multiline, lalu `tojson` untuk serialisasi
otomatis. Macro pada `data/input/shared/` menyediakan langkah dan prasyarat yang
dapat dipakai selektif. Pisahkan hasil macro dan langkah tambahan dengan baris baru.
Jangan memberi nomor langkah; processor membersihkan baris kosong dan menomorinya.
`StrictUndefined` membuat variabel yang belum didefinisikan menjadi error.

```jinja2
{% set steps %}
Buka halaman Login
Masukkan email fiktif pengguna@example.test
Klik tombol Login
{% endset %}
{{ {"test_cases": [{
  "key": "contoh-login", "feature": "Login", "scenario": "Login valid",
  "steps": steps, "expected": "Halaman utama ditampilkan"
}]} | tojson }}
```

Wajib: `key`, `feature`, `scenario`, `steps`, `expected` (string tidak kosong).
Opsional: `precondition`, `priority`, `tags` (list string), `test_data` (data JSON),
`test_type`, `prefix`. `id` hanya dibuat processor; penulisan ID dalam template ditolak.
Expected result independen dari jumlah langkah. Baris kosong dibuang, whitespace
di tepi setiap baris dibersihkan, urutan dan pemisah baris isi tetap dipertahankan.
Judul atau urutan boleh berubah; pertahankan `key` untuk identitas yang sama.

### Prefix ID per kasus

Tambahkan `prefix` pada objek kasus untuk memakai counter tersendiri dalam satu file:

```jinja2
{% set _ = ns.cases.append({
    "key": "login-success",
    "prefix": "LOGIN",
    "feature": "Login",
    "scenario": "Login valid",
    "steps": steps,
    "expected": expected
}) %}
```

Urutan prioritas: **CLI `--prefix` → prefix kasus → prefix file → `TC`**.
Prefix file ditulis dalam envelope akhir, misalnya
`{{ {"prefix": "AUTH", "test_cases": ns.cases} | tojson }}`.
Untuk memakai default, hilangkan field `prefix`; string kosong dan `none` ditolak.

Kedua template contoh sekarang menggunakan `LOGIN` untuk lima kasus Login,
`REGISTER` untuk tiga Register, dan `LOGOUT` untuk dua Logout. Hasil awal:
`LOGIN-001`–`LOGIN-005`, `REGISTER-001`–`REGISTER-003`, `LOGOUT-001`–`LOGOUT-002`.
Pada versi clean, isi prefix di data tiap block; loop meneruskannya hanya jika ada.
YAML menyertakan prefix efektif, sedangkan kolom ID Excel memuat ID lengkap.

Setiap prefix mempunyai counter dan mapping persisten sendiri; urutan kasus pada
output tetap mengikuti template. `key` tetap harus unik di seluruh file, termasuk
antar-prefix. Mengubah prefix kasus memakai mapping pada namespace baru; mapping
lama dipertahankan. Jika kembali ke prefix lama, ID lama dipakai kembali.
Untuk memberi seluruh kasus prefix yang sama: `uv run jinsey generate --prefix AUTH`.

`config/fields.yaml` adalah satu sumber opsi Priority (`P0`, `P1`, `P2`, default `P2`).
Nilai di luar opsi ditolak sebelum output ditulis. Excel memakai pencarian header
Priority, validasi list dengan error prompt, wrap text, filter, header beku, dan satu
baris per kasus. Opsi panjang atau yang mengandung koma memakai hidden lookup sheet
dan named range. Respons dropdown bergantung aplikasi Excel yang digunakan.
Teks authored selalu disimpan sebagai teks, termasuk yang diawali `=`.
Sel melebihi batas Excel 32.767 karakter ditolak agar tidak terpotong diam-diam.

## ID dan keamanan export

`.id_registry.json` di root project adalah state persisten. Simpan dan cadangkan
bersama project; jangan hapus ketika membersihkan `data/output/`. File ini diabaikan Git
agar registry lokal tidak tertukar. Untuk kolaborasi, bagikan registry secara sengaja
dan gunakan satu lokasi registry bersama. Setiap prefix memiliki pemetaan `key → ID`
dan counter monoton. Nomor minimal tiga digit (`TC-001`, setelah 999 menjadi `TC-1000`).
Key hilang diperingatkan, mapping tetap disimpan, dan ID tidak didaur ulang.
Mengganti key dianggap kasus baru; mengganti prefix memakai namespace ID berbeda.

Pipeline: render → parse JSON → validasi/normalisasi → preview ID → export sementara
→ buka ulang dan verifikasi output → commit artifact → commit registry.
File sementara/backup dibuat di direktori tujuan sehingga `os.replace` atomik per
file. Kegagalan commit yang tertangkap (termasuk interrupt) memulihkan file sebelumnya;
jika pemulihan gagal, lokasi backup dilaporkan dan dipertahankan untuk recovery.
Lock registry `.id_registry.json.lock` mencegah dua generator dengan registry sama
memberikan ID bersamaan. Gunakan registry yang sama untuk tujuan output yang sama.
Pemadaman paksa/`SIGKILL` di tengah commit beberapa file tidak dijamin atomik sebagai
satu grup; periksa backup `.jinsey-*` dan jalankan ulang dengan registry persisten.
Jangan mengedit registry manual. Registry rusak/duplikat ditolak dengan pesan spesifik.

Google Sheets merupakan adapter opsional dan belum diimplementasikan. Generasi lokal
tidak membutuhkan akun, kredensial, layanan eksternal, atau dependency Google.

## Pemeriksaan keamanan dan performa

Jalankan pemeriksaan berikut dari root project setelah `uv sync --locked`:

```bash
uv run pytest --cov=jinsey --cov-report=term-missing
uv run ruff check src tests scripts
uv run bandit -r src scripts -q
uv run pip-audit --skip-editable
uv run python scripts/benchmark.py --sizes 10 1000 3000 --repeat 3
```

`pip-audit` membutuhkan internet untuk memeriksa advisory versi package yang
terpasang; `--skip-editable` mengecualikan package Jinsey lokal, yang diperiksa lewat
review, test, dan Bandit. Audit dependency tidak mengirim source code Jinsey.
Benchmark memakai data fiktif dan direktori sementara; registry/output utama tidak diubah.

### Perlindungan yang diterapkan

- Renderer memakai `SandboxedEnvironment` dan `StrictUndefined`. Akses atribut
  internal Python dibatasi, konteks hanya menerima data JSON, dan import template
  harus tetap berada dalam direktori template, termasuk setelah resolusi symlink.
  Macro, namespace, append, dan loop pada kedua template contoh tetap bekerja.
- Source template dibatasi 4 MiB per file dan hasil render dibatasi 32 Mi karakter.
  Batas hasil diperiksa saat mengumpulkan chunk render. Batas ini tidak menjamin
  batas memori/CPU untuk satu ekspresi Jinja yang sangat mahal.
- JSON menolak properti duplikat, `NaN`, `Infinity`, dan angka float yang overflow.
  Konfigurasi YAML memakai turunan `SafeLoader` yang menolak key duplikat dan
  konstruksi objek Python. Key TC/registry tidak boleh memuat karakter kontrol.
- Sel Excel authored disimpan sebagai teks, termasuk yang diawali `=`, `+`, `-`,
  `@`, atau menyerupai error Excel. Karakter XML terlarang dan sel lebih dari
  32.767 karakter ditolak sebelum commit. Maksimum data Excel adalah 1.048.575 TC
  ditambah satu header.
- Output, registry, dan lock tidak boleh menimpa file template yang dirender,
  termasuk file yang di-import/include, atau konfigurasi field. Alias path registry
  diresolusikan sebelum locking. Lock menunggu paling lama 30 detik, kemudian
  memberikan pesan untuk mencoba kembali jika generator lain masih aktif.
- Export diverifikasi sebelum commit; kegagalan penulisan yang tertangkap memakai
  rollback. Batasan power loss/`SIGKILL` tetap seperti dijelaskan di bagian ID.
- `.env` dan varian lokalnya diabaikan Git; `.env.example` tetap dapat di-commit.

Gunakan template yang kamu tulis atau review sendiri. Sandbox Jinja merupakan
perlindungan tambahan, bukan isolasi proses/OS. Menjalankan template upload dari
pihak tidak tepercaya sebagai layanan bersama memerlukan isolasi dan batas resource
terpisah. Hal ini mengikuti [batas keamanan sandbox Jinja](https://jinja.palletsprojects.com/en/stable/sandbox/#security-considerations).

### Hasil audit dan benchmark lokal

Pemeriksaan pada 15 Oktober 2026, macOS, Python 3.12.8:

- **200 test lulus**, coverage source **99%** (termasuk mode folder dengan banyak sheet).
- Ruff dan Bandit tidak melaporkan temuan.
- pip-audit tidak menemukan advisory yang diketahui pada 42 dependency pihak ketiga
  yang terpasang. pytest diperbarui dari 8.4.2 ke 9.1.1 untuk menyelesaikan
  [advisory penanganan tmpdir](https://github.com/advisories/GHSA-6w46-j5rx-g56g);
  batas minimum dependency development kini 9.0.3.
- Kedua template contoh menghasilkan YAML dan Excel yang diverifikasi ulang.

Median tiga pengulangan benchmark sintetis, dua langkah pendek per TC:

| Jumlah TC | Export Excel saja | Pipeline penuh, termasuk YAML/Excel, verifikasi, dan registry |
| --- | --- | --- |
| 10 | 0,007 detik | 0,023 detik |
| 1.000 | 0,160 detik | 1,060 detik |
| 3.000 | 0,496 detik | 3,350 detik |

Pada fixture perbandingan 3.000 TC, export Excel turun dari 5,440 menjadi 0,507
detik setelah pemindaian ukuran worksheet berulang dihapus dan objek style dipakai
ulang, sekitar 10 kali lebih cepat. Angka ini hasil lokal, bukan batas waktu yang
dijamin; panjang isi TC, disk, hardware, dan versi Python memengaruhi hasil.
Audit advisory menggambarkan database saat diperiksa dan perlu diulang secara berkala.
Windows/Linux belum diuji langsung dalam sesi ini.
