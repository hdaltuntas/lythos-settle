[English](README.md) | **Türkçe**

# Lythos Settle

[![Tests](https://github.com/hdaltuntas/lyrhos-settle/actions/workflows/tests.yml/badge.svg)](https://github.com/hdaltuntas/lyrhos-settle/actions/workflows/tests.yml)

Tarayıcıdan sürülen, sığ temellerin oturma analizi. Tabakalı bir zemin profili üzerindeki
dikdörtgen, şerit ya da dairesel bir temelin **ne kadar** ve **ne hızla** oturacağı
hesaplanır:

1. **Gerilmeler** — yerinde σv0, u0, σ'v0 ve σ'p; temel altındaki gerilme artışı Boussinesq
   (Newmark dikdörtgen, şerit ve daire çözümleri) ya da 2:1 yayılma ile; merkez, karakteristik
   nokta, uzun kenar ortası ve köşede.
2. **Ani oturma** — tüm tabakalarda tabakalı elastik (Steinbrenner) ya da granüler
   tabakalarda Schmertmann (1978).
3. **Konsolidasyon** — kil tabakalarının Cc, Cr, e0 ve σ'p ile birincil oturması; Cα ile
   tasarım ömrüne kadar ikincil sıkışma.
4. **Zaman** — Terzaghi tek boyutlu konsolidasyonu, her kil tabakası kendi başına drene;
   t50, t90 ve zaman–oturma eğrisi.
5. **Kontroller** — toplam oturma ve açısal distorsiyon, izin verilen değerlere karşı.

Bunun üzerine bir **parametrik veya güvenilirlik çalışması** istenen girdiyi — bir aralık
ya da bir dağılım olarak — tarar; duyarlılıkları ve izin verilen oturmanın veya
distorsiyonun aşılma olasılığını, güven aralığı ve güvenilirlik indeksi β ile raporlar.

Programın tamamı — her etiket, sonuç metni, şekil ve rapor — **Türkçe ve İngilizce**
çalışır; dil çalışma sırasında değiştirilir.

Arayüz, kendi makinenizde çalışan küçük bir HTTP sunucusudur ve tarayıcıdan sürülür. Bu
sayede program uzak oturumda ya da kapsayıcı içinde de kullanılabilir ve standart kütüphane
dışında hiçbir bağımlılık getirmez.

> [LythosFEA](https://github.com/hdaltuntas/lythos),
> [Lythos Kinematic](https://github.com/hdaltuntas/lythoskinematic),
> [Lythos SPWA](https://github.com/hdaltuntas/lythosspwa) ve
> [LythosLE](https://github.com/hdaltuntas/lythosle) ile kardeştir, aynı mimariyi izler.

## Ekran görüntüleri

| Sonuç özeti | Zaman–oturma |
|---|---|
| ![Sonuç özeti](screenshots/settle_summary.png) | ![Zaman–oturma](screenshots/settle_time.png) |

| Güvenilirlik çalışması | Derinlikle oturma, koyu tema, Türkçe |
|---|---|
| ![Çalışma](screenshots/settle_study.png) | ![Derinlikle oturma](screenshots/settle_depth_dark_tr.png) |

## Kurulum ve çalıştırma

Klondan, yalnız bilimsel paketler kurulu olarak:

```bash
pip install numpy matplotlib reportlab
python main.py
```

ya da kurup komutla:

```bash
pip install .
lythos-settle                      # arayüzü tarayıcıda açar
```

Python 3.10+ gerekir. Word raporu için `python-docx`, çalışmanın tablo çıktısı için
`openpyxl` gerekir; ikisi de isteğe bağlıdır (`pip install ".[docx,xlsx]"`).

## Komut satırı

```bash
lythos-settle                                  # web arayüzü (varsayılan)
lythos-settle web --port 9000 --lang tr --no-browser
lythos-settle example -o project.settle        # başlangıç proje dosyası
lythos-settle run project.settle -o rapor.pdf --lang tr
lythos-settle study project.settle -o ornekler.csv
```

## Girdiler

* **Temel:** şekil (dikdörtgen, şerit, daire), B (dairede çap), L, derinlik Df, brüt taban
  basıncı q; isteğe bağlı olarak kazılan örtü yükü düşülür (q_net = q − σv0(Df)).
* **Yeraltı suyu:** su tablası derinliği, γw.
* **Zemin profili**, yüzeyden aşağı, her tabaka bir satır: kalınlık, granüler ya da
  kohezyonlu, γ, γdoy, E, ν; killerde ayrıca Cc, Cr, e0, OCR, cv, Cα ve tek / çift yönlü
  drenaj. E kumda drenajlı, kilde drenajsız modüldür.
* **Seçenekler:** gerilme dağılımı, ani oturma yöntemi, esnek ya da rijit temel, alt tabaka
  kalınlığı, etki derinliği oranı Δσ/σ'v0, tasarım ömrü, Schmertmann sünme katsayısı.
* **Ölçütler:** izin verilen toplam oturma ve açısal distorsiyon (1/x).

## Hesaplananlar

| büyüklük | yöntem |
|---|---|
| dikdörtgen altında Δσ | Boussinesq'in Newmark integrasyonu, her nokta için süperpozisyon |
| şerit / daire altında Δσ | kapalı form / kutupsal açı üzerinde kesin tek boyutlu integral |
| yaklaşık Δσ | 2:1 yayılma |
| ani oturma | her tabakada Steinbrenner F1, F2 (tabakalı elastik) ya da C1, C2 ve L/B'ye göre enterpole edilen etki diyagramıyla Schmertmann (1978) |
| birincil konsolidasyon | σ'p = OCR·σ'v0'a kadar Cr, ötesinde Cc; her noktada alt tabaka alt tabaka |
| ikincil sıkışma | U = %95'ten tasarım ömrüne Cα/(1+e0)·H·log(t/t_p); kilin aşırı konsolide kaldığı yerde Cα·Cr/Cc |
| zaman | kil tabakası başına Terzaghi U(Tv), H_dr = H/2 veya H |
| rijit temel | karakteristik noktanın oturması (0.74·B/2, 0.74·L/2; 0.845·R) |
| açısal distorsiyon | (s_merkez − s_kenar) / (B/2) |

Türetmeler ve sınırları [docs/theory.md](docs/theory.md) dosyasındadır.

## Raporlar

Başlıktaki listeden PDF, tek dosyalık HTML ya da Word seçip *Rapor al…* düğmesine basın.
Rapor girdileri, gerilmeleri, her noktada ve her tabakada oturmayı, Schmertmann
katsayılarını, konsolidasyon sürelerini, kontrolleri, şekilleri, uyarıları, yöntem
notlarını ve — çalıştırıldıysa — çalışmayı, arayüzün dilinde içerir.

## Geliştirme

```bash
pip install -e ".[dev]"
pytest -q
ruff check .
```

## Lisans

[MIT](LICENSE) © 2026 Hasan Deniz Altuntaş
