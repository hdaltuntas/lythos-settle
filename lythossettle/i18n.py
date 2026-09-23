"""
Every text of Lythos Settle, in English and Turkish.

Each entry is written once as ``key: (English, Turkish)`` so the two languages
cannot drift apart: a key without its translation is a syntax error, not a
blank on the screen. `TRANSLATIONS[lang][key]` is how the rest of the program
reads them.
"""

from __future__ import annotations

ENTRIES = {
    # ------------------------------------------------------------------ input errors
    "err_dimensions": ("The foundation width and length must be greater than zero.",
                       "Temel genişliği ve boyu sıfırdan büyük olmalıdır."),
    "err_pressure": ("The bearing pressure cannot be negative.",
                     "Taban basıncı negatif olamaz."),
    "err_depth": ("The foundation base must lie within the soil profile "
                  "(0 ≤ Df < depth of the profile).",
                  "Temel tabanı zemin profilinin içinde olmalıdır (0 ≤ Df < profil derinliği)."),
    "err_no_layers": ("The soil profile has no layer with a thickness.",
                      "Zemin profilinde kalınlığı girilmiş tabaka yok."),
    "err_layer_E": ("Layer '{name}': the modulus E must be greater than zero.",
                    "'{name}' tabakası: E modülü sıfırdan büyük olmalıdır."),
    "err_gamma": ("Layer '{name}': γ must be positive and γsat greater than γw.",
                  "'{name}' tabakası: γ pozitif, γdoy ise γw'den büyük olmalıdır."),
    "err_layer_nu": ("Layer '{name}': Poisson's ratio must be between 0 and 0.5.",
                     "'{name}' tabakası: Poisson oranı 0 ile 0.5 arasında olmalıdır."),
    "err_layer_e0": ("Layer '{name}': the initial void ratio e0 must be greater than zero.",
                     "'{name}' tabakası: başlangıç boşluk oranı e0 sıfırdan büyük olmalıdır."),
    "err_sublayer": ("The sublayer thickness must be greater than zero.",
                     "Alt tabaka kalınlığı sıfırdan büyük olmalıdır."),
    "err_life": ("The design life must be greater than zero.",
                 "Tasarım ömrü sıfırdan büyük olmalıdır."),

    "err_embankment": ("The embankment needs a height and a unit weight greater than zero, a crest "
                       "width of zero or more, and slope angles between 0 and 90°.",
                       "Dolgunun yüksekliği ve birim hacim ağırlığı sıfırdan büyük, tepe genişliği "
                       "sıfır veya daha büyük, şev açıları 0 ile 90° arasında olmalıdır."),

    # ------------------------------------------------------------------ warnings
    "warn_swapped": ("The length was shorter than the width; B and L were swapped so that B ≤ L.",
                     "Boy genişlikten kısaydı; B ≤ L olacak şekilde B ve L yer değiştirdi."),
    "warn_compensated": ("The net pressure is zero or negative (a compensated foundation): "
                         "no settlement is computed.",
                         "Net basınç sıfır ya da negatif (dengelenmiş temel): oturma hesaplanmadı."),
    "warn_below_profile": ("The stress increase is still significant at the base of the profile "
                           "({depth:.1f} m); the soil below it is taken as incompressible.",
                           "Gerilme artışı profil tabanında ({depth:.1f} m) hâlâ önemli; altındaki "
                           "zemin sıkışmaz kabul edildi."),
    "warn_no_cc": ("Cohesive layer '{name}' has no Cc or Cr: its consolidation settlement is zero.",
                   "Kohezyonlu '{name}' tabakasında Cc veya Cr yok: konsolidasyon oturması sıfır."),
    "warn_no_cv": ("Cohesive layer '{name}' has no cv: it is taken as consolidating at once.",
                   "Kohezyonlu '{name}' tabakasında cv yok: konsolidasyonun hemen tamamlandığı "
                   "kabul edildi."),
    "warn_no_tp": ("Layer '{name}' has Cα but no cv, so the end of primary consolidation is "
                   "unknown: its secondary compression is not computed.",
                   "'{name}' tabakasında Cα var ama cv yok; birincil konsolidasyonun sonu "
                   "bilinmediğinden ikincil sıkışma hesaplanmadı."),
    "warn_ocr": ("Layer '{name}': an OCR below 1 (under-consolidation) is not supported; "
                 "OCR = 1 was used.",
                 "'{name}' tabakası: 1'den küçük OCR (eksik konsolidasyon) desteklenmez; "
                 "OCR = 1 alındı."),
    "warn_schmertmann_zone": ("Schmertmann's influence zone extends below the soil profile; "
                              "the part below it is ignored.",
                              "Schmertmann etki bölgesi zemin profilinin altına uzanıyor; "
                              "altta kalan kısım hesaba katılmadı."),

    "warn_emb_schmertmann": ("Schmertmann's method is for footings; the embankment's immediate "
                             "settlement is computed elastically (Steinbrenner).",
                             "Schmertmann yöntemi tekil temeller içindir; dolgunun ani oturması "
                             "elastik olarak (Steinbrenner) hesaplandı."),

    # ------------------------------------------------------------------ choice labels
    "shape_rectangle": ("Rectangle", "Dikdörtgen"),
    "shape_strip": ("Strip", "Şerit"),
    "shape_circle": ("Circle", "Daire"),
    "shape_embankment": ("Embankment (fill)", "Dolgu (şevli)"),
    "stress_boussinesq": ("Boussinesq (elastic)", "Boussinesq (elastik)"),
    "stress_two_to_one": ("2:1 spread", "2:1 yayılma"),
    "immediate_elastic": ("Elastic (Steinbrenner)", "Elastik (Steinbrenner)"),
    "immediate_schmertmann": ("Schmertmann (granular layers)", "Schmertmann (granüler tabakalar)"),
    "rigidity_flexible": ("Flexible", "Esnek"),
    "rigidity_rigid": ("Rigid", "Rijit"),
    "behaviour_granular": ("Granular", "Granüler"),
    "behaviour_cohesive": ("Cohesive", "Kohezyonlu"),
    "drainage_double": ("Double", "Çift yönlü"),
    "drainage_single": ("Single", "Tek yönlü"),
    "point_center": ("Centre", "Merkez"),
    "point_char": ("Characteristic point", "Karakteristik nokta"),
    "point_edge": ("Middle of long edge", "Uzun kenar ortası"),
    "point_corner": ("Corner", "Köşe"),
    "point_shoulder": ("Crest edge", "Tepe kenarı"),
    "point_midslope": ("Middle of the slope", "Şev ortası"),
    "point_toe": ("Toe of the slope", "Şev topuğu"),
    "method_elastic": ("Elastic (Steinbrenner)", "Elastik (Steinbrenner)"),
    "method_schmertmann": ("Schmertmann", "Schmertmann"),
    "method_cohesive": ("Undrained elastic + consolidation", "Drenajsız elastik + konsolidasyon"),

    # ------------------------------------------------------------------ input groups
    "group_project": ("Project", "Proje"),
    "title_label": ("Title", "Başlık"),
    "analyst_label": ("Analyst", "Hazırlayan"),
    "group_foundation": ("Foundation", "Temel"),
    "shape_label": ("Shape", "Şekil"),
    "B_label": ("Width B (diameter of a circle)", "Genişlik B (dairede çap)"),
    "L_label": ("Length L (rectangle)", "Boy L (dikdörtgen)"),
    "Df_label": ("Foundation depth Df", "Temel derinliği Df"),
    "q_label": ("Bearing pressure q (gross)", "Taban basıncı q (brüt)"),
    "net_label": ("Deduct the excavated overburden (net pressure)",
                  "Kazılan örtü yükünü düş (net basınç)"),
    "group_embankment": ("Embankment", "Dolgu"),
    "emb_crest_label": ("Crest width", "Tepe genişliği"),
    "emb_height_label": ("Height H", "Yükseklik H"),
    "emb_slope_left_label": ("Left slope angle", "Sol şev açısı"),
    "emb_slope_right_label": ("Right slope angle", "Sağ şev açısı"),
    "emb_gamma_label": ("Unit weight of the fill γ", "Dolgunun birim hacim ağırlığı γ"),
    "emb_note": ("A long fill on the ground surface (plane strain): γ·H under the crest, falling to "
                 "zero at the toes. Slope angles from the horizontal: 1V:2H = 26.57°, "
                 "1V:1.5H = 33.69°.",
                 "Zemin yüzeyindeki uzun bir dolgu (düzlem şekil değiştirme): tepe altında γ·H, "
                 "topuklarda sıfıra iner. Şev açıları yataydan: 1D:2Y = 26.57°, 1D:1.5Y = 33.69°."),
    "group_water": ("Groundwater", "Yeraltı suyu"),
    "water_depth_label": ("Water table depth", "Su tablası derinliği"),
    "gamma_w_label": ("Unit weight of water γw", "Suyun birim hacim ağırlığı γw"),
    "group_options": ("Analysis options", "Analiz seçenekleri"),
    "stress_method_label": ("Stress distribution", "Gerilme dağılımı"),
    "immediate_method_label": ("Immediate settlement", "Ani oturma"),
    "rigidity_label": ("Foundation rigidity", "Temel rijitliği"),
    "sublayer_label": ("Sublayer thickness", "Alt tabaka kalınlığı"),
    "depth_ratio_label": ("Influence depth ratio Δσ / σ'v0", "Etki derinliği oranı Δσ / σ'v0"),
    "design_life_label": ("Design life", "Tasarım ömrü"),
    "creep_label": ("Schmertmann creep factor C2", "Schmertmann sünme katsayısı C2"),
    "options_note": ("Settlement is summed down to the depth where Δσ falls to the given fraction "
                     "of σ'v0 (0: the whole profile). A rigid foundation settles as its "
                     "characteristic point.",
                     "Oturma, Δσ'nın σ'v0'ın verilen oranına düştüğü derinliğe kadar toplanır "
                     "(0: tüm profil). Rijit temel, karakteristik noktası kadar oturur."),
    "group_criteria": ("Criteria", "Ölçütler"),
    "s_allow_label": ("Allowable total settlement", "İzin verilen toplam oturma"),
    "distortion_label": ("Allowable angular distortion 1 /", "İzin verilen açısal distorsiyon 1 /"),
    "criteria_note": ("Enter 0 to leave a check out.", "Bir kontrolü kapatmak için 0 girin."),

    # ------------------------------------------------------------------ soil table
    "col_name": ("Layer", "Tabaka"),
    "col_thickness": ("t (m)", "t (m)"),
    "col_behaviour": ("Type", "Tür"),
    "col_gamma": ("γ (kN/m³)", "γ (kN/m³)"),
    "col_gamma_sat": ("γsat (kN/m³)", "γdoy (kN/m³)"),
    "col_E": ("E (MPa)", "E (MPa)"),
    "col_nu": ("ν", "ν"),
    "col_Cc": ("Cc", "Cc"),
    "col_Cr": ("Cr", "Cr"),
    "col_e0": ("e0", "e0"),
    "col_OCR": ("OCR", "OCR"),
    "col_cv": ("cv (m²/yr)", "cv (m²/yıl)"),
    "col_Calpha": ("Cα", "Cα"),
    "col_drainage": ("Drainage", "Drenaj"),
    "soil_note": ("E is the drained modulus of a granular layer and the undrained modulus of a "
                  "cohesive one. Cc, Cr, e0, OCR, cv, Cα and drainage apply to cohesive layers.",
                  "E, granüler tabakada drenajlı, kohezyonlu tabakada drenajsız modüldür. Cc, Cr, "
                  "e0, OCR, cv, Cα ve drenaj kohezyonlu tabakalar içindir."),

    # ------------------------------------------------------------------ summary cards
    "card_total": ("Total settlement", "Toplam oturma"),
    "card_total_sub": ("{point}", "{point}"),
    "card_immediate": ("Immediate", "Ani"),
    "card_consolidation": ("Consolidation", "Konsolidasyon"),
    "card_secondary": ("Secondary ({life:g} yr)", "İkincil ({life:g} yıl)"),
    "card_at_life": ("After {life:g} years", "{life:g} yıl sonunda"),
    "card_time": ("Time to 90 % consolidation", "%90 konsolidasyon süresi"),
    "card_distortion": ("Angular distortion", "Açısal distorsiyon"),
    "card_check_total": ("Settlement check", "Oturma kontrolü"),
    "card_check_dist": ("Distortion check", "Distorsiyon kontrolü"),
    "card_none": ("—", "—"),
    "ok_short": ("OK", "UYGUN"),
    "notok_short": ("NOT OK", "UYGUN DEĞİL"),
    "na_short": ("n/a", "—"),

    # ------------------------------------------------------------------ results text
    "res_title": ("SETTLEMENT ANALYSIS RESULTS", "OTURMA ANALİZİ SONUÇLARI"),
    "res_foundation": ("Foundation: {shape}, B = {B:.2f} m{L}, Df = {Df:.2f} m, {rigidity}",
                       "Temel: {shape}, B = {B:.2f} m{L}, Df = {Df:.2f} m, {rigidity}"),
    "res_embankment": ("Embankment: crest {c:.2f} m, height {h:.2f} m, slopes {sl:.1f}° / {sr:.1f}°, "
                       "γ = {g:.1f} kN/m³, base width {w:.2f} m",
                       "Dolgu: tepe {c:.2f} m, yükseklik {h:.2f} m, şevler {sl:.1f}° / {sr:.1f}°, "
                       "γ = {g:.1f} kN/m³, taban genişliği {w:.2f} m"),
    "res_emb_load": ("Fill load q = γ·H = {q:.1f} kPa under the crest",
                     "Dolgu yükü q = γ·H = {q:.1f} kPa (tepe altında)"),
    "res_emb_dist": ("Embankment: the angular distortion is not checked.",
                     "Dolgu: açısal distorsiyon kontrol edilmez."),
    "card_dist_emb": ("not checked for a fill", "dolguda kontrol edilmez"),
    "res_pressure": ("Gross pressure q = {q:.1f} kPa; overburden at the base σv0 = {s:.1f} kPa; "
                     "net pressure q_net = {qn:.1f} kPa",
                     "Brüt basınç q = {q:.1f} kPa; taban seviyesinde örtü yükü σv0 = {s:.1f} kPa; "
                     "net basınç q_net = {qn:.1f} kPa"),
    "res_methods": ("Stress distribution: {stress}; immediate settlement: {imm}",
                    "Gerilme dağılımı: {stress}; ani oturma: {imm}"),
    "res_limit": ("Influence depth: {z:.2f} m below ground ({zb:.2f} m below the base)",
                  "Etki derinliği: zeminden {z:.2f} m (taban altında {zb:.2f} m)"),
    "res_points_title": ("Settlement at the evaluation points (mm)",
                         "Hesap noktalarında oturma (mm)"),
    "res_layers_title": ("Settlement by layer, {point} (mm)", "Tabakalara göre oturma, {point} (mm)"),
    "res_time_title": ("Consolidation time", "Konsolidasyon süresi"),
    "res_time_line": ("{name}: H_dr = {h:.2f} m, cv = {cv:.2f} m²/yr, t50 = {t50}, t90 = {t90}",
                      "{name}: H_dr = {h:.2f} m, cv = {cv:.2f} m²/yıl, t50 = {t50}, t90 = {t90}"),
    "res_at_life": ("Settlement after {life:g} years: {s:.1f} mm",
                    "{life:g} yıl sonundaki oturma: {s:.1f} mm"),
    "res_schm": ("Schmertmann: C1 = {c1:.3f}, C2 = {c2:.3f}, Izp = {izp:.3f} at {zp:.2f} m, "
                 "influence zone to {ze:.2f} m below the base",
                 "Schmertmann: C1 = {c1:.3f}, C2 = {c2:.3f}, Izp = {izp:.3f} ({zp:.2f} m'de), "
                 "etki bölgesi taban altında {ze:.2f} m'ye kadar"),
    "res_checks_title": ("Checks", "Kontroller"),
    "res_check_total": ("Total settlement {s:.1f} mm, allowable {a:.1f} mm: {status}",
                        "Toplam oturma {s:.1f} mm, izin verilen {a:.1f} mm: {status}"),
    "res_check_dist": ("Angular distortion {x}, allowable {a}: {status}",
                       "Açısal distorsiyon {x}, izin verilen {a}: {status}"),
    "res_rigid": ("Rigid foundation: the settlement is read at the characteristic point, and the "
                  "distortion is not checked.",
                  "Rijit temel: oturma karakteristik noktada okunur, distorsiyon kontrol edilmez."),
    "res_compensated": ("Compensated foundation: no settlement.", "Dengelenmiş temel: oturma yok."),
    "head_point": ("Point", "Nokta"),
    "head_layer": ("Layer", "Tabaka"),
    "head_immediate": ("Immediate", "Ani"),
    "head_consolidation": ("Consol.", "Konsol."),
    "head_secondary": ("Secondary", "İkincil"),
    "head_total": ("Total", "Toplam"),
    "warnings_title": ("Warnings", "Uyarılar"),
    "unit_days": ("{v:.0f} days", "{v:.0f} gün"),
    "unit_years": ("{v:.1f} years", "{v:.1f} yıl"),
    "run_analysis_button": ("Run analysis", "Analizi çalıştır"),
    "running_analysis": ("Analysing…", "Analiz ediliyor…"),
    "analysis_complete": ("Analysis complete.", "Analiz tamamlandı."),
    "report_action": ("Export report…", "Rapor al…"),
    "report_running": ("Writing the report…", "Rapor hazırlanıyor…"),

    # ------------------------------------------------------------------ figures
    "fig_schematic": ("Section and stress bulb", "Kesit ve gerilme soğanı"),
    "fig_stress": ("Stresses with depth", "Derinlikle gerilmeler"),
    "fig_influence": ("Influence factors", "Etki katsayıları"),
    "fig_settlement_depth": ("Settlement with depth", "Derinlikle oturma"),
    "fig_time": ("Time–settlement", "Zaman–oturma"),
    "fig_points": ("Settlement at the points", "Noktalarda oturma"),
    "fig_profile": ("Settlement across the section", "Kesit boyunca oturma"),
    "lg_emb_load": ("q = γH = {q:.0f} kPa", "q = γH = {q:.0f} kPa"),
    "ax_depth": ("Depth below ground (m)", "Zeminden derinlik (m)"),
    "ax_stress": ("Vertical stress (kPa)", "Düşey gerilme (kPa)"),
    "ax_influence": ("Δσ / q_net,  Iz", "Δσ / q_net,  Iz"),
    "ax_cumulative": ("Settlement of the soil below this depth (mm)",
                      "Bu derinliğin altındaki zeminin oturması (mm)"),
    "ax_settlement": ("Settlement (mm)", "Oturma (mm)"),
    "ax_time": ("Time (years)", "Zaman (yıl)"),
    "ax_x": ("Distance from the centre (m)", "Merkezden uzaklık (m)"),
    "lg_sigma_eff": ("σ'v0 in situ", "σ'v0 yerinde"),
    "lg_final": ("σ'v0 + Δσ", "σ'v0 + Δσ"),
    "lg_sigma_p": ("σ'p (cohesive)", "σ'p (kohezyonlu)"),
    "lg_limit": ("{r:g} · σ'v0", "{r:g} · σ'v0"),
    "lg_dsigma": ("Δσ ({point})", "Δσ ({point})"),
    "lg_primary": ("Immediate + primary", "Ani + birincil"),
    "lg_total": ("Total (with secondary)", "Toplam (ikincil dahil)"),
    "lg_allow": ("Allowable", "İzin verilen"),
    "lg_life": ("Design life", "Tasarım ömrü"),
    "lg_water": ("Water table", "Su tablası"),
    "lg_iz": ("Schmertmann Iz", "Schmertmann Iz"),
    "lg_zlimit": ("Influence depth", "Etki derinliği"),
    "lg_t90": ("t90 {name}", "t90 {name}"),
    "lg_isobar": ("Δσ / q_net isobars (Boussinesq)", "Δσ / q_net eş gerilme eğrileri (Boussinesq)"),
    "lg_qnet": ("q_net = {q:.0f} kPa", "q_net = {q:.0f} kPa"),

    # ------------------------------------------------------------------ study
    "group_study": ("Study options", "Çalışma seçenekleri"),
    "study_method": ("Sampling", "Örnekleme"),
    "study_n": ("Samples (LHS / Monte Carlo)", "Örnek sayısı (LHS / Monte Carlo)"),
    "study_seed": ("Random seed", "Rastgele tohum"),
    "study_note": ("One-at-a-time sweeps the range variables one by one; Latin hypercube and Monte "
                   "Carlo sample every variable together (a range as a uniform distribution).",
                   "Tek tek tarama, aralık değişkenlerini sırayla tarar; Latin hiperküp ve Monte "
                   "Carlo tüm değişkenleri birlikte örnekler (aralık düzgün dağılım olarak)."),
    "method_oat": ("One at a time", "Tek tek tarama"),
    "method_lhs": ("Latin hypercube", "Latin hiperküp"),
    "method_mc": ("Monte Carlo", "Monte Carlo"),
    "dist_normal": ("Normal", "Normal"),
    "dist_lognormal": ("Lognormal", "Lognormal"),
    "dist_uniform": ("Uniform", "Düzgün"),
    "col_param": ("Input", "Girdi"),
    "col_mode": ("Mode", "Mod"),
    "col_min": ("Min", "Min"),
    "col_max": ("Max", "Maks"),
    "col_dist": ("Distribution", "Dağılım"),
    "col_mean": ("Mean", "Ortalama"),
    "col_cov": ("CoV", "CoV"),
    "col_points": ("Points", "Nokta"),
    "mode_range": ("Range", "Aralık"),
    "mode_dist": ("Distribution", "Dağılım"),
    "study_run": ("Run study", "Çalışmayı başlat"),
    "study_cancel": ("Cancel", "İptal"),
    "study_export_csv": ("Export CSV", "CSV dışa aktar"),
    "study_export_xlsx": ("Export XLSX", "XLSX dışa aktar"),
    "study_vars_group": ("Study variables", "Çalışma değişkenleri"),
    "study_no_vars": ("Add at least one study variable.", "En az bir çalışma değişkeni ekleyin."),
    "study_progress": ("{done} / {total} samples", "{done} / {total} örnek"),
    "study_done": ("Study finished: {n} samples.", "Çalışma tamamlandı: {n} örnek."),
    "study_cancelled": ("(cancelled)", "(iptal edildi)"),
    "study_failed": ("The study could not start: {e}", "Çalışma başlatılamadı: {e}"),
    "study_no_data": ("No study results yet.", "Henüz çalışma sonucu yok."),
    "study_table_note": ("Only the first rows are shown; export the table for all of them.",
                         "Yalnız ilk satırlar gösterilir; tamamı için tabloyu dışa aktarın."),
    "study_fig_oat": ("One-at-a-time sweep", "Tek tek tarama"),
    "study_fig_hist": ("Histogram", "Histogram"),
    "study_fig_scatter": ("Scatter", "Saçılım"),
    "study_fig_tornado": ("Sensitivity (tornado)", "Duyarlılık (tornado)"),
    "out_s_total": ("Total settlement (mm)", "Toplam oturma (mm)"),
    "out_s_imm": ("Immediate settlement (mm)", "Ani oturma (mm)"),
    "out_s_cons": ("Consolidation settlement (mm)", "Konsolidasyon oturması (mm)"),
    "out_s_sec": ("Secondary compression (mm)", "İkincil sıkışma (mm)"),
    "out_beta": ("Angular distortion (‰)", "Açısal distorsiyon (‰)"),
    "out_t90": ("t90 of the slowest layer (years)", "En yavaş tabakanın t90'ı (yıl)"),
    "out_error": ("Error", "Hata"),
    "ls_settlement": ("Settlement > allowable", "Oturma > izin verilen"),
    "ls_distortion": ("Distortion > allowable", "Distorsiyon > izin verilen"),
    "st_title": ("STUDY RESULTS", "ÇALIŞMA SONUÇLARI"),
    "st_info": ("Method: {method}; samples: {n}; successful: {ok}",
                "Yöntem: {method}; örnek: {n}; başarılı: {ok}"),
    "st_stats_title": ("Statistics of the outputs", "Çıktıların istatistikleri"),
    "st_rel_title": ("Probability of exceeding the criteria", "Ölçütlerin aşılma olasılığı"),
    "st_rel_line": ("{name}: {k} of {n}, P = {pf:.3g} (95 % CI {lo:.3g} – {hi:.3g}), β = {beta}",
                    "{name}: {n} örnekte {k}, P = {pf:.3g} (%95 GA {lo:.3g} – {hi:.3g}), β = {beta}"),
    "st_sens_title": ("Sensitivity of the total settlement (Spearman ρ)",
                      "Toplam oturmanın duyarlılığı (Spearman ρ)"),
    "st_no_sens": ("Sensitivities need at least three samples of a sampled variable.",
                   "Duyarlılık için örneklenen değişkenin en az üç örneği gerekir."),
    "st_mean": ("mean", "ort."),
    "st_std": ("std", "std"),
    "var_q": ("q", "q"),
    "var_B": ("B", "B"),
    "var_L": ("L", "L"),
    "var_Df": ("Df", "Df"),
    "var_depth": ("water table", "su tablası"),
    "var_thickness": ("t", "t"),
    "var_gamma": ("γ", "γ"),
    "var_gamma_sat": ("γsat", "γdoy"),
    "var_E": ("E", "E"),
    "var_nu": ("ν", "ν"),
    "var_Cc": ("Cc", "Cc"),
    "var_Cr": ("Cr", "Cr"),
    "var_e0": ("e0", "e0"),
    "var_OCR": ("OCR", "OCR"),
    "var_cv": ("cv", "cv"),
    "var_Calpha": ("Cα", "Cα"),
    "var_crest": ("crest width", "tepe genişliği"),
    "var_height": ("H", "H"),
    "var_slope_left": ("left slope", "sol şev"),
    "var_slope_right": ("right slope", "sağ şev"),
    "grp_embankment": ("Embankment", "Dolgu"),
    "grp_foundation": ("Foundation", "Temel"),
    "grp_water": ("Groundwater", "Yeraltı suyu"),
}

TRANSLATIONS = {
    "en": {key: pair[0] for key, pair in ENTRIES.items()},
    "tr": {key: pair[1] for key, pair in ENTRIES.items()},
}


def t(lang: str, key: str, **params) -> str:
    """One text in one language, formatted; the key itself if it is unknown."""
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
    return text.format(**params) if params else text


def warning_text(lang: str, warning) -> str:
    """An engine warning, (key, params), as a sentence."""
    key, params = warning
    return t(lang, key, **params)
