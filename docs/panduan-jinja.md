# Panduan Jinja untuk menulis test case

[Kembali ke README](../README.md)

Belum menyiapkan Python dan uv? Ikuti [setup Windows, Linux, dan macOS](../README.md#setup-windows-linux-dan-macos)
terlebih dahulu. Tidak ada plugin editor yang wajib untuk generate.

Mulai dari versi **lengkap / non-clean** jika ingin membaca semua isi satu TC
di satu tempat. Setelah terbiasa, gunakan versi **clean** untuk memakai ulang
langkah dan prasyarat yang sama.

## Daftar isi

- [File yang perlu dikenali](#file-yang-perlu-dikenali)
- [Cara menjalankan file pilihan](#cara-menjalankan-file-pilihan)
- [Menggabungkan satu folder menjadi banyak sheet](#menggabungkan-satu-folder-menjadi-banyak-sheet)
- [Membaca tanda-tanda Jinja](#membaca-tanda-tanda-jinja)
- [Arti field test case](#arti-field-test-case)
- [Versi lengkap / non-clean](#versi-lengkap--non-clean)
- [Versi clean dan active_account](#versi-clean-dan-active_account)
- [Cara menambah atau mengubah TC](#cara-menambah-atau-mengubah-tc)
- [Prefix dan ID otomatis](#prefix-dan-id-otomatis)
- [Kesalahan yang sering terjadi](#kesalahan-yang-sering-terjadi)

## File yang perlu dikenali

| File | Gunanya | Kapan diedit? |
| --- | --- | --- |
| [testcases.j2](../data/input/testcases.j2) | Versi lengkap; isi setiap TC langsung di satu block | Mengubah TC pada versi lengkap |
| [testcases_clean.j2](../data/input/testcases_clean.j2) | Versi clean; lima Login memakai langkah/prasyarat bersama | Mengubah TC pada versi clean |
| [shared/login_steps.j2](../data/input/shared/login_steps.j2) | Menyimpan macro langkah awal Login | Mengubah langkah yang dipakai bersama |
| [shared/preconditions.j2](../data/input/shared/preconditions.j2) | Menyimpan macro prasyarat | Mengubah prasyarat yang dipakai bersama |
| [fields.yaml](../config/fields.yaml) | Opsi dan default Priority | Mengubah konfigurasi pilihan |
| `data/output/testcases/` | YAML/Excel dari versi lengkap | Dibaca untuk memeriksa hasil |
| `data/output/testcases_clean/` | YAML/Excel dari versi clean | Dibaca untuk memeriksa hasil |
| `.id_registry.json` | Mengingat pasangan key, prefix, dan ID antar-run | Dikelola generator; jangan dihapus saat membersihkan output |

Kedua template contoh awalnya berisi 10 kasus yang sama. Keduanya adalah file
terpisah: mengedit versi lengkap tidak otomatis mengubah versi clean, dan sebaliknya.
Pilih satu sebagai sumber yang kamu pakai. Mengedit hasil YAML/Excel tidak mengubah
template, dan perubahan hasil tersebut akan tertimpa saat generate berikutnya.

Alurnya:

```text
Edit file .j2 → validate → generate → periksa YAML dan Excel
```

## Cara menjalankan file pilihan

Jalankan terminal dari root project, yaitu folder yang berisi `pyproject.toml`.
Saat pertama kali menyiapkan project:

```bash
uv sync --locked
```

Untuk versi lengkap:

```bash
uv run jinsey validate --template testcases.j2
uv run jinsey generate --template testcases.j2
```

Untuk versi clean:

```bash
uv run jinsey validate --template testcases_clean.j2
uv run jinsey generate --template testcases_clean.j2
```

**`uv run jinsey generate` tanpa `--template` membaca `data/input/testcases.j2`.**
File yang sedang aktif di editor tidak menentukan file yang digenerate.
Hasil otomatis dipisah menurut nama file template:

| Perintah | Sumber | Folder hasil |
| --- | --- | --- |
| `uv run jinsey generate` | `data/input/testcases.j2` | `data/output/testcases/` |
| `uv run jinsey generate --template testcases_clean.j2` | `data/input/testcases_clean.j2` | `data/output/testcases_clean/` |

Setiap folder hasil berisi `testcases.yaml` dan `testcases.xlsx`. CLI juga mencetak
`Template: ...` sehingga kamu tahu sumber yang dipakai. File input cukup ditulis
namanya; CLI mencarinya di `data/input/`. Jika ingin file di lokasi lain, berikan path
eksplisit seperti `--template ./custom.j2` atau path absolut.

Untuk menentukan folder hasil sendiri:

```bash
uv run jinsey generate --template testcases.j2 --output-dir data/output/lengkap
uv run jinsey generate --template testcases_clean.j2 --output-dir data/output/clean
```

`validate` hanya memeriksa isi; tidak menulis output atau memberi ID baru.
`generate` memberi ID, membuat output, lalu membuka ulang hasilnya untuk verifikasi.
`generate --dry-run` menampilkan rencana ID tanpa menulis file.
Jinsey tidak membuka browser atau menjalankan langkah pengujian aplikasi.

## Menggabungkan satu folder menjadi banyak sheet

Jika satu folder berisi `satu.j2`, `dua.j2`, dan `tiga.j2`, kamu bisa membuat
satu workbook dengan sheet `dua`, `satu`, dan `tiga` (urut alfabetis).
Setiap file ditulis dengan struktur Jinja yang sama seperti contoh di panduan ini;
pilihan clean atau lengkap tidak mengubah cara penggabungannya.

Misalnya file berada di `data/input/suite_saya/`, jalankan:

```bash
uv run jinsey validate --input-dir suite_saya
uv run jinsey generate --input-dir suite_saya --format excel
```

Hasilnya `data/output/suite_saya/testcases.xlsx`. Sheet memakai nama file tanpa
`.j2`, sedangkan jumlah baris mengikuti jumlah TC di masing-masing file.
Untuk mencoba contoh yang sudah ada di repository:

```bash
uv run jinsey generate --input-dir auth_suite --format all
```

Contoh ini menghasilkan lima sheet dengan total 10 TC, ditambah satu YAML yang
mengelompokkan TC berdasarkan sheet. Gunakan `--format excel` jika hanya ingin Excel.

Tempatkan helper macro/include di `shared/` di dalam folder suite; subfolder tidak
diubah menjadi sheet. Tiap key harus unik antarfile. Nama file tanpa `.j2` harus
memenuhi batas nama sheet Excel (maksimal 31 karakter). ID otomatis, prefix,
dropdown, dan verifikasi output tetap digunakan. Detail aturan dan daftar contoh
ada di [panduan mode folder pada README](../README.md#satu-folder-menjadi-satu-workbook-dengan-banyak-sheet).

## Membaca tanda-tanda Jinja

Jinja adalah template teks. Dalam project ini, kita memakainya untuk menyusun
daftar TC; Python kemudian memvalidasi dan mengekspor daftar tersebut.

| Bentuk | Arti dalam bahasa sehari-hari |
| --- | --- |
| `{# catatan #}` | Komentar untuk pembaca; tidak masuk ke hasil |
| `{% ... %}` | Instruksi, misalnya menyimpan teks atau mengulang data |
| `{{ ... }}` | Menuliskan nilai/hasil pemanggilan ke teks template |
| `{% set steps %} ... {% endset %}` | Simpan teks beberapa baris dengan nama `steps` |
| `{% block login_success %} ... {% endblock login_success %}` | Batas bagian bernama untuk satu TC |
| `{% import "shared/preconditions.j2" as pre %}` | Buka kumpulan macro dan beri nama singkat `pre` |
| `pre.active_account()` | Panggil macro `active_account` dari kumpulan `pre` |
| `{% for example in ns.login_examples %} ... {% endfor %}` | Kerjakan isi blok untuk setiap data Login |
| `{% if "prefix" in example %} ... {% endif %}` | Jalankan bagian ini hanya jika data mempunyai prefix |
| `value \| tojson` | Ubah nilai menjadi JSON dengan pengutipan otomatis |

`block` bukan field output dan namanya bukan ID test case. Gunakan nama unik
seperti `login_success`; nama block tidak boleh memakai strip `-`.
`key` boleh memakai strip, misalnya `login-success`. Keduanya merupakan nama
berbeda dengan tugas berbeda; saat membuat TC baru, ubah keduanya agar unik.

Isi block diindentasi agar mudah dibaca. Editor yang mendukung Jinja dapat memakai
struktur tersebut untuk folding/Sticky Scroll; tampilannya bergantung dukungan editor.

### Mengapa ada namespace, append, dan tanda underscore?

```jinja2
{% set ns = namespace(cases=[]) %}
```

Artinya: siapkan wadah bernama `ns`, dengan daftar `cases` yang masih kosong.
`[]` berarti daftar kosong. Satu objek `{ ... }` berisi pasangan nama field dan nilainya.

```jinja2
{% set _ = ns.cases.append(case) %}
```

Artinya: tambahkan satu objek `case` ke daftar TC. `_` menampung hasil operasi
yang tidak perlu ditampilkan. Jangan ganti baris ini menjadi `{{ ... }}`, karena
kita sedang mengumpulkan data, bukan mencetak hasil operasi `append`.

Variabel `set` di dalam suatu block bersifat lokal pada block itu. Namespace
menjaga daftar yang ditambahkan tetap tersedia di luar block. Karena itu, pada versi
clean, data Login disimpan ke `ns.login_examples` sebelum dibaca oleh loop bersama.

Terakhir, baris berikut mengubah seluruh daftar menjadi satu dokumen JSON:

```jinja2
{{ {"test_cases": ns.cases} | tojson }}
```

Letakkan **satu kali di akhir file**, setelah seluruh TC dan loop perakitan selesai.
Tidak perlu menulis JSON atau karakter `\n` secara manual dalam isi langkah.

## Arti field test case

Nama field harus ditulis persis seperti berikut; misalnya `precondition` dalam
bentuk tunggal, bukan `preconditions`, dan `expected`, bukan `expected_result`.

| Field | Wajib? | Isi / contoh |
| --- | --- | --- |
| `key` | Ya | Identitas tetap dan unik, misalnya `login-success`; dipakai registry |
| `prefix` | Tidak | Awalan ID, misalnya `LOGIN`; jika absen mengikuti prefix file atau `TC` |
| `feature` | Ya | Fitur yang diuji, misalnya `Login` |
| `scenario` | Ya | Judul kasus, misalnya `Login dengan kredensial valid` |
| `precondition` | Tidak | Kondisi sebelum langkah dimulai; default teks kosong |
| `steps` | Ya | Langkah yang dilakukan; string berisi satu atau beberapa baris |
| `expected` | Ya | Hasil yang harus diamati; string berisi satu atau beberapa baris |
| `priority` | Tidak | `P0`, `P1`, `P2`; default `P2` dari konfigurasi saat ini |
| `tags` | Tidak | Daftar label, misalnya `["smoke", "positive"]`; default `[]` |
| `test_data` | Tidak | Data pendukung seperti `{"email": "pengguna@example.test"}`; default `none` |
| `test_type` | Tidak | Teks jenis pengujian, misalnya `positive` atau `negative`; default teks kosong |
| `id` | Dibuat generator | Muncul di output; jangan ditambahkan sebagai field input |

`steps` dan `expected` harus berisi teks. Jumlah baris hasil yang diharapkan tidak
harus sama dengan jumlah langkah. Tulis hasil berdasarkan perilaku aplikasi yang
ingin diuji; generator tidak menentukan ekspektasi bisnis untukmu.

Indentasi tepi baris dan baris kosong dibersihkan oleh processor. Langkah kemudian
diberi nomor otomatis. Misalnya:

```jinja2
{% set steps %}
    Buka halaman Login
    Klik tombol Login
{% endset %}
```

menjadi isi sel Steps:

```text
1. Buka halaman Login
2. Klik tombol Login
```

## Versi lengkap / non-clean

Pada [testcases.j2](../data/input/testcases.j2), setiap block berisi prasyarat,
langkah, hasil, lalu objek data yang ditambahkan ke `ns.cases`.

Berikut contoh **file lengkap**. Untuk mencoba, simpan sebagai
`data/input/belajar_lengkap.j2`; ini contoh baru, tidak mengganti file yang sudah ada.

```jinja2
{% set ns = namespace(cases=[]) %}

{% block login_demo %}
    {% set precondition %}
        Akun fiktif pengguna@example.test sudah terdaftar dan aktif
        Pengguna belum memiliki sesi aktif
    {% endset %}

    {% set steps %}
        Buka halaman Login aplikasi fiktif Lentera
        Pastikan formulir Login ditampilkan
        Masukkan email pengguna@example.test
        Masukkan password fiktif Valid!234
        Klik tombol Login
    {% endset %}

    {% set expected %}
        Pengguna berhasil masuk
        Halaman utama ditampilkan
    {% endset %}

    {% set _ = ns.cases.append({
        "key": "login-demo",
        "prefix": "LOGIN",
        "feature": "Login",
        "scenario": "Contoh Login valid",
        "precondition": precondition,
        "steps": steps,
        "expected": expected,
        "priority": "P1",
        "tags": ["fictional", "positive"],
        "test_data": {"email": "pengguna@example.test"},
        "test_type": "positive"
    }) %}
{% endblock login_demo %}

{{ {"test_cases": ns.cases} | tojson }}
```

Bagian `"steps": steps` berarti field output bernama `steps` mengambil nilai
dari variabel `steps` yang ditulis di atas. Jika ditulis `"steps": "steps"`,
isinya justru menjadi kata **steps**, bukan daftar langkah.

Tidak ada import atau macro di contoh ini; seluruh isi dapat dibaca dalam satu file.
Untuk TC baru, salin satu block sebelum baris `tojson`, ganti nama block dan key,
lalu isi scenario, precondition, steps, expected, dan data lainnya.

## Versi clean dan active_account

Pada [testcases_clean.j2](../data/input/testcases_clean.j2), langkah yang sama
diletakkan di file shared, agar tidak perlu ditulis berulang kali.
Perubahan macro akan memengaruhi semua kasus yang memanggil macro itu.

### Apa itu active_account()?

Dalam [shared/preconditions.j2](../data/input/shared/preconditions.j2) ada:

```jinja2
{% macro active_account() -%}
Akun fiktif pengguna@example.test sudah terdaftar dan aktif
Pengguna belum memiliki sesi aktif
{%- endmacro %}
```

`macro` adalah potongan template yang bisa dipanggil berulang. Nama `active_account`
dibuat oleh penulis project, bukan perintah bawaan khusus Jinja atau Python.
Macro tersebut **hanya menghasilkan teks prasyarat**, tidak membuat akun dan
tidak memeriksa kondisi aplikasi sungguhan.

Setelah import:

```jinja2
{% import "shared/preconditions.j2" as pre %}
```

kamu dapat memasukkan hasilnya langsung ke field:

```jinja2
"precondition": pre.active_account(),
```

Tanda kurung `()` berarti memanggil macro. Hasilnya sama dengan menulis dua baris
prasyarat tadi secara langsung. Jika ingin menampilkannya dalam blok teks, gunakan
`{{ pre.active_account() }}`. Tanda `-` pada `{%-` / `-%}` dalam definisi macro
mengatur pembersihan whitespace di sekitar batas macro; tidak berkaitan dengan ID.

Macro lain yang tersedia:

| Panggilan | Teks yang disediakan | Dipakai untuk |
| --- | --- | --- |
| `pre.active_account()` | Akun aktif dan belum memiliki sesi | Lima kasus Login |
| `pre.signed_in()` | Pengguna sudah masuk dan halaman utama ditampilkan | Kasus Logout |
| `login.open_login()` | Buka halaman Login dan pastikan formulir tampil | Langkah awal lima kasus Login |

Alias `pre` dan `login` berasal dari baris `import ... as ...` dalam template.
Path import dicari relatif terhadap folder file template, sehingga kedua file
contoh utama berada di `data/input/` dan memakai `data/input/shared/`.

### Cara lima kasus Login dirangkai

```text
Block per Login → ns.login_examples → loop perakitan → ns.cases → tojson
```

`ns.login_examples` menyimpan data khusus tiap Login. `ns.cases` menyimpan objek TC
yang sudah lengkap. Keduanya disiapkan oleh:

```jinja2
{% set ns = namespace(cases=[], login_examples=[]) %}
```

Berbeda dengan field input akhir, data sementara Login memakai nama berikut:

| Data sementara | Menjadi field akhir |
| --- | --- |
| `key` | `key` |
| `title` | `scenario` |
| `action` | Digabung dengan `login.open_login()` menjadi `steps` |
| `expected` | `expected` |
| `type` | `test_type`, juga salah satu label pada `tags` |
| `priority` | `priority` |
| `prefix` jika diisi | `prefix` |

Jadi `title`, `action`, dan `type` adalah nama data perantara dalam template clean,
bukan field baru yang boleh dikirim langsung ke processor.
Pada loop yang ada, `feature`, `precondition`, `tags`, dan `test_data` diisi bersama.
Menambah `precondition` pada record sementara saja tidak mengubah hasil; loop juga
harus diubah untuk membaca field tersebut. Untuk alur yang berbeda, kamu bisa
menambahkan TC langsung ke `ns.cases`, seperti Register dan Logout yang sudah ada.

Berikut contoh **file clean lengkap** untuk dicoba sebagai
`data/input/belajar_clean.j2`. Contoh ini menghasilkan kasus yang sama dengan
`belajar_lengkap.j2`, memakai macro shared yang sudah tersedia.

```jinja2
{% import "shared/login_steps.j2" as login %}
{% import "shared/preconditions.j2" as pre %}
{% set ns = namespace(cases=[], login_examples=[]) %}

{% block login_demo %}
    {% set action %}
        Masukkan email pengguna@example.test
        Masukkan password fiktif Valid!234
        Klik tombol Login
    {% endset %}

    {% set expected %}
        Pengguna berhasil masuk
        Halaman utama ditampilkan
    {% endset %}

    {% set _ = ns.login_examples.append({
        "key": "login-demo",
        "prefix": "LOGIN",
        "title": "Contoh Login valid",
        "action": action,
        "expected": expected,
        "priority": "P1",
        "type": "positive"
    }) %}
{% endblock login_demo %}

{% for example in ns.login_examples %}
    {% set steps %}
        {{ login.open_login() }}
        {{ example.action }}
    {% endset %}

    {% set case = {
        "key": example.key,
        "feature": "Login",
        "scenario": example.title,
        "precondition": pre.active_account(),
        "steps": steps,
        "expected": example.expected,
        "priority": example.priority,
        "tags": ["fictional", example.type],
        "test_data": {"email": "pengguna@example.test"},
        "test_type": example.type
    } %}
    {% if "prefix" in example %}
        {% set _ = case.update({"prefix": example.prefix}) %}
    {% endif %}
    {% set _ = ns.cases.append(case) %}
{% endfor %}

{{ {"test_cases": ns.cases} | tojson }}
```

Pertahankan baris baru antara `{{ login.open_login() }}` dan `{{ example.action }}`.
Jika keduanya ditempel tanpa pemisah, akhir langkah bersama bisa menyatu dengan
langkah khusus. Penomoran dilakukan setelah semuanya digabungkan.

Register dan Logout di template clean saat ini langsung masuk ke `ns.cases`.
Logout memakai `pre.signed_in()`; Register mempunyai langkah sendiri.
Kamu tidak harus menggunakan alur Login untuk fitur lain.

## Cara menambah atau mengubah TC

### Mengubah kasus yang sudah ada

1. Tentukan template yang akan dipakai pada `--template`.
2. Cari block berdasarkan key, misalnya `login_success` untuk `login-success`.
3. Pada versi lengkap, edit teks `precondition`, `steps`, atau `expected` di block itu.
4. Pada versi clean, edit `action`/`expected` untuk Login; edit file shared jika
   perubahan memang berlaku bagi seluruh pemanggil. Register/Logout diedit pada block-nya.
5. Pertahankan `key` jika kasusnya masih merupakan kasus yang sama.
6. Jalankan `validate`, kemudian `generate`, lalu buka hasil YAML/Excel.

### Menambah Login pada versi clean

1. Salin satu block Login, misalnya dari `block login_success` sampai `endblock login_success`.
2. Tempel **sebelum** bagian `LOGIN — PERAKITAN BERSAMA` dan loop `for example ...`.
3. Ganti nama block dan key agar unik; sesuaikan judul, langkah khusus, hasil, priority, dan prefix.
4. Pastikan objek ditambahkan ke `ns.login_examples`, seperti block Login lainnya.
5. Jangan menambahkan `login.open_login()` lagi ke `action`: loop sudah menyediakannya.
6. Pertahankan loop perakitan satu kali; loop akan memproses seluruh data Login.

Nama variabel lokal seperti `success_action` boleh sama di block berbeda karena
scope-nya terpisah. Jika diganti menjadi `new_action`, ubah juga referensi `"action": new_action`.
Block yang diletakkan setelah loop tidak ikut diproses oleh loop yang sudah selesai.

### Menambah kasus dengan alur lain

Salin pola block Register/Logout atau contoh lengkap di atas, lalu tambahkan objeknya
langsung ke `ns.cases`. Letakkan setelah loop Login dan sebelum baris `tojson` akhir.
Isi prasyarat dan langkah yang sesuai, gunakan macro hanya jika isinya memang relevan.
Jika tidak perlu prasyarat, hilangkan field `precondition` atau isi teks kosong `""`.

Urutan output mengikuti urutan penambahan ke `ns.cases`. Pada versi clean saat ini,
lima Login ditambahkan saat loop, lalu Register, kemudian Logout.

### Mencoba file belajar tanpa mengubah registry utama

Setelah menyimpan contoh file lengkap di atas pada `data/input/`:

```bash
uv run jinsey validate --template belajar_lengkap.j2
uv run jinsey generate --template belajar_lengkap.j2 --output-dir data/output/belajar-lengkap --registry data/output/belajar-state/ids.json

uv run jinsey validate --template belajar_clean.j2
uv run jinsey generate --template belajar_clean.j2 --output-dir data/output/belajar-clean --registry data/output/belajar-state/ids.json
```

Keduanya sengaja memakai registry latihan yang sama agar kasus `login-demo`
mendapat ID yang sama. Registry latihan ini terpisah dari `.id_registry.json` utama.
Jika latihan ingin dilanjutkan dengan ID tetap, pertahankan `data/output/belajar-state/`.
Contoh file belajar belum dibuat otomatis; salin potongan **file lengkap** yang sesuai.

## Prefix dan ID otomatis

Tulis `"prefix": "LOGIN"` dalam objek TC atau data sementara Login.
Counter masing-masing prefix terpisah:

| Prefix | Contoh ID awal |
| --- | --- |
| `LOGIN` | `LOGIN-001`, `LOGIN-002` |
| `REGISTER` | `REGISTER-001`, `REGISTER-002` |
| `LOGOUT` | `LOGOUT-001`, `LOGOUT-002` |

Urutan pilihan prefix: **CLI `--prefix` → field kasus → prefix file → default `TC`**.
Hilangkan field `prefix` untuk memakai fallback; jangan menggantinya dengan `""` atau `none`.
Prefix menerima huruf besar, angka, underscore, dimulai huruf, maksimum 32 karakter.

Jika ingin default seluruh file berupa `AUTH`, ganti envelope akhir menjadi:

```jinja2
{{ {"prefix": "AUTH", "test_cases": ns.cases} | tojson }}
```

Kasus yang sudah mempunyai `"prefix": "LOGIN"` tetap memakai `LOGIN`. Untuk
memaksa seluruh kasus menjadi `AUTH`, jalankan:

```bash
uv run jinsey generate --template testcases_clean.j2 --prefix AUTH
```

Nomor tidak ditentukan dari nama block atau komentar ID di template. Generator
mengingat `key` dalam namespace prefix di registry. Mengubah judul atau mengurutkan
ulang kasus mempertahankan ID. Mengganti key berarti identitas baru. Mengganti
prefix memakai namespace berbeda; mapping lama tetap disimpan. Kasus yang dihapus
tidak menyebabkan ID-nya diberikan ke kasus baru.

## Kesalahan yang sering terjadi

| Gejala / pesan | Yang perlu diperiksa |
| --- | --- |
| Hasil berbeda dari tab yang sedang dibuka | Pastikan argumen `--template`; tab aktif editor tidak memilih input |
| `duplicate key` | Beri setiap TC key unik, termasuk antar-prefix |
| Block didefinisikan dua kali | Ubah nama pada `block` dan `endblock` hasil salinan |
| `undefined` | Periksa ejaan variabel, import, nama macro, dan tanda kurung pemanggilan |
| `missing or invalid required field` | Periksa lima field wajib dan pastikan string berisi teks |
| `invalid priority` | Gunakan opsi dalam `config/fields.yaml`, saat ini `P0/P1/P2` |
| `Invalid prefix` | Gunakan format prefix yang valid atau hilangkan field untuk fallback |
| `id is generated` | Hapus field `id` dari objek input; komentar referensi boleh tetap ada |
| `unknown fields` untuk `title`, `action`, atau `type` | Data sementara Login harus melalui loop, bukan langsung dimasukkan ke `ns.cases` |
| Langkah menjadi kata `steps` | Gunakan `"steps": steps`, bukan `"steps": "steps"` |
| Dua langkah menyatu | Pisahkan pemanggilan macro dan langkah berikutnya dengan baris baru |
| TC Login baru tidak muncul | Letakkan block baru sebelum loop, dan periksa `ns.login_examples.append(...)` |
| Hasil edit YAML hilang | Edit sumber `.j2`, kemudian generate ulang |

Saat menyalin objek `{ ... }`, pertahankan koma antar-field serta pasangan kurung.
Gunakan blok `set` untuk teks multiline dan `tojson` sekali di akhir; keduanya
menangani penyusunan teks tanpa menulis escape newline secara manual.

[Kembali ke README](../README.md)
