"""DevClean çoklu dil (Türkçe / İngilizce) yerelleştirme yöneticisi."""

from __future__ import annotations

from PyQt6.QtCore import QObject, QSettings, pyqtSignal


TRANSLATIONS: dict[str, dict[str, str]] = {
    "tr": {
        # Genel / Birimler
        "unit_zero_bytes": "0 Bayt",
        "unit_bytes": "Bayt",
        "unknown": "Bilinmiyor",
        "unspecified": "Belirtilmemiş",
        "ready": "Hazır",
        "ok": "Tamam",
        "cancel": "İptal",
        "yes": "Evet",
        "no": "Hayır",
        "category_word": "Kategori",
        "active_tag": "[Etkin]",

        # Kapsam (Scope)
        "scope_sys64": "Sistem (64-bit)",
        "scope_sys32": "Sistem (32-bit)",
        "scope_user": "Kullanıcı",

        # Pencere ve Menüler
        "app_subtitle": "Disk ve Geliştirici Yönetimi",
        "menu_file": "&Dosya",
        "menu_refresh_view": "Etkin Görünümü Yenile",
        "menu_exit": "Çıkış",
        "menu_view": "&Görünüm",
        "menu_refresh_drives": "Disk Durumunu Güncelle",
        "menu_language": "&Dil (Language)",
        "menu_help": "&Yardım",
        "menu_about": "DevClean Hakkında",
        "lang_tr": "Türkçe",
        "lang_en": "English",
        "sidebar_sections": "Denetim Masası Bölümleri",
        "sidebar_language": "Arayüz Dili",
        "sidebar_drives": "Sabit Disk Durumu",
        "nav_apps": "Yüklü Uygulamalar",
        "nav_caches": "Geçici Geliştirici Dosyaları",
        "nav_devtools": "Geliştirme Araçları ve SDK'lar",

        # Sürücü Kartı
        "drive_title": "Yerel Disk ({drive})",
        "drive_sub": "{free} boş, toplam {total}",

        # Hakkında Penceresi
        "about_title": "DevClean Hakkında",
        "about_html": (
            "<b>DevClean</b><br>"
            "Sürüm 1.1<br><br>"
            "Geliştirici Disk Temizleme, Yüklü Uygulama ve SDK Yönetimi Aracı.<br><br>"
            "• Yüksek disk alanı kullanan yüklü uygulamaları inceleme ve kaldırma<br>"
            "• Geçici geliştirici dizinlerini (<code>.venv</code>, <code>.cache</code>, <code>.nuget</code>, "
            "<code>__pycache__</code>, <code>node_modules</code>, <code>.gradle</code>) temizleme<br>"
            "• Visual Studio, VS SDK'ları (.NET ve Windows Kits), Python, PyCharm ve Android Studio yönetimi"
        ),

        # Ortak Komutlar ve Hatalar
        "btn_uninstall": "Kaldır",
        "btn_modify": "Değiştir",
        "btn_modify_repair": "Değiştir / Onar",
        "btn_open_location": "Dosya Konumunu Aç",
        "btn_refresh": "Yenile",
        "err_no_uninstall_cmd": "Kaldırma komutu tanımlı değil.",
        "err_invalid_uninstaller": "Geçerli bir kaldırıcı yolu çözümlenemedi.",
        "msg_uninstaller_started": "Resmi kaldırma aracı başlatıldı.",
        "err_uninstaller_failed": "Kaldırıcı başlatılamadı: {error}",
        "err_elevated_win_only": "Yükseltilmiş çalıştırma yalnızca Windows üzerinde desteklenir.",
        "err_uac_cancelled": "Kaldırma işlemi başlatılamadı veya yönetici onayı iptal edildi.",
        "err_path_missing": "Belirtilen yol mevcut değil.",
        "err_protected_runtime": "Çalışmakta olan Python ortamı güvenlik nedeniyle silinemez.",
        "msg_moved_to_recycle": "Geri Dönüşüm Kutusu'na taşındı.",
        "err_recycle_failed": "Geri Dönüşüm Kutusu işlemi tamamlanamadı (Kod: 0x{code:X}). Dosyalar kullanımda olabilir.",
        "msg_deleted_perm": "Kalıcı olarak silindi.",
        "err_delete_failed": "Silme hatası: {error}",
        "msg_folder_not_found": "Belirtilen klasör diskte bulunamadı.",

        # Sekme 1: Yüklü Uygulamalar
        "apps_banner_title": "Yüklü Uygulamalar ve Disk Kullanımı",
        "apps_banner_sub": (
            "Çok yer kaplayan uygulamaları boyuta göre sıralayın. "
            "Bir uygulamayı kaldırmak için listeden seçip Kaldır düğmesini tıklatın."
        ),
        "apps_chk_calc_sizes": "Eksik boyutları diskten hesapla",
        "apps_chk_calc_sizes_tip": (
            "Kayıt defterinde boyutu belirtilmeyen uygulamaların kurulum klasörü boyutunu hesaplar."
        ),
        "apps_lbl_size_filter": "Boyut:",
        "apps_filter_all": "Tüm Boyutlar",
        "apps_filter_100mb": "100 MB ve üzeri",
        "apps_filter_500mb": "500 MB ve üzeri",
        "apps_filter_1gb": "1 GB ve üzeri",
        "apps_filter_5gb": "5 GB ve üzeri",
        "apps_search_ph": "Uygulama veya yayıncı ara...",
        "apps_col_name": "Ad",
        "apps_col_publisher": "Yayıncı",
        "apps_col_size": "Boyut",
        "apps_col_date": "Yüklenme Tarihi",
        "apps_col_version": "Sürüm",
        "apps_col_scope": "Kapsam",
        "apps_scanning": "Yüklü uygulamalar okunuyor...",
        "apps_scanning_reg": "Kayıt defterindeki yüklü uygulamalar okunuyor...",
        "apps_calc_folder": "Klasör boyutu hesaplanıyor: {name}",
        "apps_scan_done_status": "Toplam {count} yüklü uygulama listelendi ({size}).",
        "apps_calculated_suffix": " (klasörden hesaplandı)",
        "apps_det_default_title": "Yüklü Uygulamalar",
        "apps_det_publisher": "Yayıncı: {val}",
        "apps_det_version": "Sürüm: {val}",
        "apps_det_size": "Disk Boyutu: {val}",
        "apps_det_location": "Konum: {val}",
        "apps_sum_count": "Gösterilen Uygulama: {count} adet",
        "apps_sum_size": "Toplam Kaplanan Alan: {size}",
        "apps_sum_sort_tip": "Sıralama: Sütun başlıklarına tıklayarak değiştirebilirsiniz",
        "apps_sum_unins_tip": "Bilgi: Kaldırma işlemi uygulamanın resmi kaldırıcısını başlatır",
        "apps_confirm_title": "DevClean — Uygulama Kaldırma Onayı",
        "apps_confirm_body": (
            "'{name}' uygulamasını kaldırmak için resmi kaldırma aracı başlatılsın mı?\n\n"
            "Yayıncı: {publisher}\n"
            "Tahmini Boyut: {size}\n"
            "Komut: {cmd}"
        ),
        "apps_unins_err_title": "DevClean — Kaldırıcı Başlatılamadı",
        "apps_mod_err_title": "DevClean — Değiştirme Aracı Başlatılamadı",
        "apps_no_loc_msg": "Bu uygulama için geçerli bir kurulum klasörü bulunamadı.",

        # Sekme 2: Geçici Geliştirici Dosyaları
        "caches_banner_title": "Geçici Geliştirici Dosyaları ve Önbellek Temizleme",
        "caches_banner_sub": (
            "Sanal ortamları (.venv), paket önbelleklerini (.cache, .nuget, pip, npm, Gradle) "
            "ve derleme çıktılarını inceleyip güvenle temizleyin."
        ),
        "caches_btn_rescan": "Yeniden Tara",
        "caches_btn_roots": "Taranan Klasörler...",
        "caches_btn_recycle": "Geri Dönüşüm Kutusu'na Taşı",
        "caches_btn_delete_perm": "Kalıcı Olarak Sil",
        "caches_btn_select_all": "Tümünü Seç",
        "caches_btn_clear_sel": "Seçimi Temizle",
        "caches_search_ph": ".venv, .cache, .nuget veya proje ara...",
        "caches_sel_summary": "Seçilen temizlenecek alan: {size} ({count} öğe)",
        "caches_roots_hint": "Genel önbellekler + {count} proje dizini taranıyor",
        "caches_col_name": "Önbellek / Geçici Klasör",
        "caches_col_size": "Boyut",
        "caches_col_files": "Dosya Sayısı",
        "caches_col_modified": "Son Değişiklik",
        "caches_col_path": "Tam Konum",
        "caches_dirs_count": "{count} dizin",
        "caches_scanning_status": "Geçici geliştirici dosyaları (.venv, .cache, .nuget vb.) taranıyor...",
        "caches_scan_global": "Genel önbellek taranıyor: {name}",
        "caches_scan_dir": "Dizin taranıyor: {path}",
        "caches_calc_size": "Boyut hesaplanıyor: {path}",
        "caches_cleaning_item": "Temizleniyor: {path}",
        "caches_scan_done_status": "Tarama tamamlandı: {count} geçici geliştirici klasörü bulundu ({size}).",
        "caches_det_default_title": "Geçici Geliştirici Dosyaları",
        "caches_sum_total": "Bulunan Toplam Önbellek: {size} ({count} klasör)",
        "caches_sum_selected": "Seçilen Temizlenecek Alan: {size} ({count} klasör)",
        "caches_sum_scope": "Kapsam: .venv, .cache, .nuget, __pycache__, node_modules, .gradle, pip, npm",
        "caches_sum_tip": "Öneri: Güvenli geri alma için 'Geri Dönüşüm Kutusu'na Taşı' seçeneğini kullanabilirsiniz",
        "caches_cat_det_size": "Kategori Toplam Boyutu: {size}",
        "caches_cat_det_files": "Toplam Dosya Sayısı: {count}",
        "caches_cat_det_dirs": "Alt Klasör Sayısı: {count}",
        "caches_cat_det_tip": "Bu kategorideki tüm öğeleri kutucuğu işaretleyerek seçebilirsiniz.",
        "caches_item_det_cat": "Kategori: {cat} ({group})",
        "caches_item_det_size": "Boyut: {size} ({files} dosya)",
        "caches_item_det_desc": "Açıklama: {desc}",
        "caches_item_det_path": "Konum: {path}",
        "caches_group_global": "Genel Önbellek",
        "caches_group_project": "Proje Klasörü",
        "caches_confirm_recycle_title": "Geri Dönüşüm Kutusu'na Taşıma Onayı",
        "caches_confirm_perm_title": "Kalıcı Olarak Silme Onayı",
        "caches_confirm_recycle_desc": "Seçilen klasörler Windows Geri Dönüşüm Kutusu'na taşınacaktır.",
        "caches_confirm_perm_desc": "Seçilen klasörler Geri Dönüşüm Kutusu kullanılmadan diskten KALICI olarak silinecektir.",
        "caches_confirm_more": "... ve {count} klasör daha",
        "caches_confirm_body": (
            "{desc}\n\n"
            "Seçilen Klasör Sayısı: {count}\n"
            "Toplam Boyut: {size}\n\n"
            "{preview}\n\n"
            "İşleme devam edilsin mi?"
        ),
        "caches_done_title": "DevClean — Temizleme Tamamlandı",
        "caches_warn_title": "DevClean — Temizleme Sonucu",
        "caches_done_summary": (
            "Temizleme işlemi tamamlandı.\n\n"
            "Temizlenen Klasör: {count} adet\n"
            "Açılan Disk Alanı: {size}"
        ),
        "caches_done_skipped": "Bazı klasörler kullanımda olduğu için atlandı:",
        "caches_done_more_err": "... ({count} ek hata)",

        # Taranan Klasörler Diyaloğu
        "roots_dlg_title": "DevClean — Taranacak Proje Klasörleri",
        "roots_dlg_info": (
            "Geçici geliştirici klasörleri (.venv, .cache, .nuget, __pycache__, node_modules vb.) "
            "aşağıdaki proje dizinlerinde aranır:"
        ),
        "roots_btn_add": "Klasör Ekle...",
        "roots_btn_remove": "Seçileni Çıkar",
        "roots_btn_reset": "Varsayılanlara Sıfırla",
        "roots_pick_title": "Proje Klasörü Seçin",

        # Önbellek Kategorileri ve Açıklamaları
        "ccat_nuget": "NuGet Önbelleği (.nuget)",
        "ccat_cache": "Genel Önbellek (.cache)",
        "ccat_py_venv": "Python Sanal Ortamı (.venv)",
        "ccat_py_cache": "Python Önbellekleri",
        "ccat_node_cache": "Node.js ve Web Önbellekleri",
        "ccat_node_modules": "Node.js Bağımlılıkları (node_modules)",
        "ccat_gradle": "Gradle / Java / Android Önbellekleri",
        "ccat_rust_go": "Rust / Go Derleme Önbellekleri",
        "ccat_ide": "IDE Geçici Önbellekleri",
        "ccat_build_out": "Derleme Çıktıları (target / obj)",

        "cname_nuget_pkgs": "NuGet Genel Paket Önbelleği (.nuget\\packages)",
        "cdesc_nuget_pkgs": "İndirilen NuGet paketlerinin kullanıcı önbelleği. Derleme sırasında gerektiğinde yeniden indirilir.",
        "cname_nuget_v3": "NuGet HTTP v3 Önbelleği",
        "cdesc_nuget_v3": "NuGet paket kaynağı meta veri önbelleği.",
        "cname_nuget_scratch": "NuGet Geçici Klasörü (NuGetScratch)",
        "cdesc_nuget_scratch": "NuGet paket çıkarma işlemleri sırasında oluşan geçici dosyalar.",
        "cname_user_cache": "Kullanıcı .cache Dizini (~\\.cache)",
        "cdesc_user_cache": "Çeşitli geliştirme araçlarının (pip, pre-commit, HuggingFace, Playwright vb.) ortak önbellek dizini.",
        "cname_pip_cache": "Pip Paket İndirme Önbelleği",
        "cdesc_pip_cache": "pip tarafından indirilen .whl ve kaynak arşivlerinin yerel önbelleği.",
        "cname_uv_cache": "uv Paket Yöneticisi Önbelleği",
        "cdesc_uv_cache": "uv Python paket yöneticisinin tekerlek (wheel) ve arşiv önbelleği.",
        "cname_poetry_cache": "Poetry Önbelleği",
        "cdesc_poetry_cache": "Poetry paket yöneticisinin indirme önbelleği.",
        "cname_npm_local": "npm Önbelleği (Local)",
        "cdesc_npm_local": "npm paket yöneticisi önbellek dosyaları.",
        "cname_npm_roaming": "npm Önbelleği (Roaming)",
        "cdesc_npm_roaming": "Eski sürüm npm önbellek dizini.",
        "cname_yarn_cache": "Yarn Önbelleği",
        "cdesc_yarn_cache": "Yarn paket yöneticisi önbelleği.",
        "cname_pnpm_cache": "pnpm Önbelleği",
        "cdesc_pnpm_cache": "pnpm meta veri ve indirme önbelleği.",
        "cname_gradle_caches": "Gradle Derleme Önbelleği (~\\.gradle\\caches)",
        "cdesc_gradle_caches": "Android Studio ve Java projelerinin paylaşılan Gradle bağımlılık ve yapı önbelleği.",
        "cname_gradle_daemon": "Gradle Daemon Günlükleri (~\\.gradle\\daemon)",
        "cdesc_gradle_daemon": "Arka plan Gradle derleme süreçlerine ait eski günlük dosyaları.",
        "cname_maven_repo": "Maven Yerel Deposu (~\\.m2\\repository)",
        "cdesc_maven_repo": "Maven tarafından indirilen .jar bağımlılık arşivi.",
        "cname_cargo_cache": "Cargo Kayıt Önbelleği (~\\.cargo\\registry\\cache)",
        "cdesc_cargo_cache": "Rust Cargo tarafından indirilen sıkıştırılmış .crate arşivleri.",
        "cname_go_build": "Go Derleme Önbelleği (go-build)",
        "cdesc_go_build": "Go derleyicisinin artımlı derleme önbelleği.",
        "cname_vs_pkgs": "Visual Studio Kurulum Paket Önbelleği",
        "cdesc_vs_pkgs": "Visual Studio kullanıcı düzeyindeki geçici bileşen önbelleği.",
        "cname_jb_caches": "JetBrains {ide} Dizin Önbelleği",
        "cdesc_jb_caches": "{ide} indeksleme önbelleği (silinirse açılışta yeniden oluşturulur).",
        "cname_jb_logs": "JetBrains {ide} Günlük Dosyaları",
        "cdesc_jb_logs": "{ide} tanılama ve hata günlükleri.",
        "cdesc_ws_venv": "Python sanal ortam dizini (requirements.txt ile yeniden kurulabilir).",
        "cdesc_ws_cache": "Proje içi geçici araç ve derleyici önbelleği.",
        "cdesc_ws_nuget": "Proje içi yerel NuGet önbellek dizini.",
        "cdesc_ws_pycache": "Python derlenmiş bayt kodu / test / analiz önbelleği ({folder}).",
        "cdesc_ws_nodemod": "Node.js proje paket dizini (npm/pnpm/yarn install ile yeniden kurulabilir).",
        "cdesc_ws_vs": "Visual Studio çözüm IntelliSense ve çalışma alanı önbelleği (.vs).",
        "cdesc_ws_gradle": "Proje içi yerel Gradle yapı önbelleği (.gradle).",
        "cdesc_ws_target": "Rust Cargo veya Maven derleme çıktı dizini (target).",
        "cdesc_ws_obj": ".NET / MSBuild ara derleme dosyaları dizini (obj).",

        # Sekme 3: Geliştirme Araçları ve SDK'lar
        "dev_banner_title": "Geliştirme Araçları, Programlama Dilleri ve SDK Yönetimi",
        "dev_banner_sub": (
            "Visual Studio, VS SDK'ları (.NET ve Windows Kits), Python, PyCharm ve Android Studio "
            "kurulumlarını ve SDK bileşenlerini yönetin veya kaldırın."
        ),
        "dev_btn_modify_workloads": "Değiştir / İş Yükleri",
        "dev_btn_remove_folder": "Bileşen Klasörünü Sil",
        "dev_btn_remove_folder_tip": (
            "Kayıt defteri kaldırıcısı bulunmayan SDK alt bileşenlerini "
            "(Android System Image, NDK, AVD, eski IDE verileri) siler."
        ),
        "dev_btn_vs_installer": "VS Installer",
        "dev_btn_vs_installer_tip": "Microsoft Visual Studio Installer aracını açar.",
        "dev_filter_all_cats": "Tüm Kategoriler",
        "dev_search_ph": "Araç, dil veya SDK ara...",
        "dev_col_name": "Bileşen / Dil / IDE",
        "dev_col_kind": "Tür",
        "dev_col_version": "Sürüm",
        "dev_col_size": "Boyut",
        "dev_col_location": "Kurulum Konumu",
        "dev_empty_category": "Bu kategoride kurulu bileşen algılanmadı",
        "dev_scanning_status": "Geliştirme dilleri ve SDK bileşenleri taranıyor...",
        "dev_scan_vs": "Visual Studio kurulumları denetleniyor...",
        "dev_scan_reg": "Kayıt defterindeki geliştirme araçları ve SDK'lar taranıyor...",
        "dev_scan_sdks": "VS SDK'ları (.NET SDK ve Windows Kits) taranıyor...",
        "dev_scan_python": "Python dağıtımları taranıyor...",
        "dev_scan_pycharm": "PyCharm kurulumları ve veri dizinleri taranıyor...",
        "dev_scan_android": "Android Studio, Android SDK ve emülatör imajları taranıyor...",
        "dev_scan_other": "Diğer programlama dilleri ve araç zincirleri taranıyor...",
        "dev_scan_done_status": "Geliştirme araçları taraması tamamlandı: {count} bileşen ({size}).",
        "dev_det_default_title": "Geliştirme Araçları ve SDK Yönetimi",
        "dev_det_cat_kind": "Kategori: {cat} ({kind})",
        "dev_det_ver_pub": "Sürüm: {ver} | Yayıncı: {pub}",
        "dev_det_size_note": "Boyut: {size} | Not: {note}",
        "dev_det_location": "Konum: {loc}",
        "dev_sum_count": "Algılanan Geliştirme Bileşeni: {count} adet",
        "dev_sum_size": "Toplam Geliştirme Ortamı Boyutu: {size}",
        "dev_sum_envs": "Yönetilen Ortamlar: Visual Studio, VS SDKs, Python, PyCharm, Android Studio",
        "dev_sum_tip": "İşlem: Bir bileşen seçerek resmi kaldırıcıyı çalıştırabilir veya SDK klasörlerini temizleyebilirsiniz",
        "dev_confirm_unins_title": "DevClean — Geliştirme Aracı Kaldırma Onayı",
        "dev_confirm_unins_body": (
            "'{name}' bileşenini kaldırmak için resmi kaldırma işlemi başlatılsın mı?\n\n"
            "Kategori: {cat}\n"
            "Boyut: {size}\n"
            "Komut: {cmd}"
        ),
        "dev_mod_err_title": "DevClean — Yönetim Aracı Başlatılamadı",
        "dev_del_folder_title": "DevClean — SDK / Veri Klasörü Silme Onayı",
        "dev_del_folder_q": "'{name}' bileşenine ait klasörü nasıl silmek istiyorsunuz?",
        "dev_del_folder_info": "Konum: {loc}\nBoyut: {size}\nBilgi: {note}",
        "dev_del_err_title": "DevClean — Klasör Silinemedi",
        "dev_ctx_modify": "Değiştir / İş Yüklerini Yönet",
        "dev_ctx_del_folder": "Bileşen Klasörünü Sil...",

        # DevTool Kategorileri
        "dcat_vs": "Visual Studio",
        "dcat_vs_sdks": "VS SDK'ları (.NET ve Windows Kits)",
        "dcat_python": "Python",
        "dcat_pycharm": "PyCharm",
        "dcat_android": "Android Studio ve Android SDK",
        "dcat_other": "Diğer Geliştirme Dilleri ve Araçları",

        # DevTool Türleri (Kind)
        "dkind_ide": "IDE",
        "dkind_ide_build": "IDE / Yapı Aracı",
        "dkind_lang": "Programlama Dili",
        "dkind_sdk": "SDK / Geliştirme Kiti",
        "dkind_sdk_sub": "SDK Alt Bileşeni",
        "dkind_ide_data": "IDE Veri Klasörü",
        "dkind_avd": "Emülatör Sanal Cihazı",
        "dkind_jdk": "JDK / Java",
        "dkind_vcs": "Sürüm Kontrol Aracı",
        "dkind_build": "Derleme Aracı",

        # DevTool Notları ve Özel İsimler
        "dnote_vswhere": "Visual Studio Installer üzerinden iş yükleri değiştirilebilir veya kaldırılabilir.",
        "dnote_dotnet_sdk": "Paylaşılan .NET SDK dizini. Kayıtlı MSI paketi varsa üstteki SDK girdisinden veya Visual Studio Installer ile kaldırılmalıdır.",
        "dname_win_sdk_ver": "Windows 10/11 SDK Başlık ve Kitaplıkları ({ver})",
        "dnote_win_sdk_ver": "Windows Kits\\10 altında Include, Lib ve bin ({ver}) bileşenleri.",
        "dname_win_kits10": "Windows Kits 10 Araçları",
        "dnote_win_kits10": "Windows Kits 10 kurulum dizini.",
        "dnote_py_active": "Etkin Python çalışma ortamı (DevClean tarafından kullanılıyor).",
        "dnote_py_exe": "Yorumlayıcı yolu: {exe}",
        "dname_py_store": "Python {ver} (Microsoft Store Dağıtımı)",
        "dnote_py_store": "Microsoft Store Appx paketi ve kullanıcı site-packages verileri.",
        "dname_py_active_interp": "Python {ver} (Etkin Yorumlayıcı)",
        "dnote_pycharm_user": "Kullanıcı dizinindeki PyCharm kurulumu.",
        "dname_pycharm_cache": "{folder} (Önbellek ve İndeks Verisi)",
        "dnote_pycharm_cache": "PyCharm önbellek ve indeks verisi dizini. Eski sürüme aitse güvenle silinebilir.",
        "dname_pycharm_cfg": "{folder} (Ayarlar ve Eklentiler)",
        "dnote_pycharm_cfg": "PyCharm ayarlar ve eklentiler dizini. Eski sürüme aitse güvenle silinebilir.",
        "dnote_android_studio": "Android Studio IDE kurulum klasörü.",
        "dname_android_sysimg": "Android Sistem İmajı (System Image) — {ver}",
        "dname_android_ndk": "Android NDK — {ver}",
        "dname_android_plat": "Android Platform SDK — {ver}",
        "dname_android_bt": "Android Build-Tools — {ver}",
        "dnote_android_sub": "Android SDK ({folder}) bileşeni. Kullanılmayan eski API sürümleri silinebilir.",
        "dname_android_emu": "Android Emulator Motoru",
        "dnote_android_emu": "Android SDK emülatör çalışma zamanı dosyaları.",
        "dname_android_avd": "Android Sanal Cihaz (AVD): {name}",
        "dpub_user_avd": "Kullanıcı AVD",
        "dnote_android_avd": "Android emülatör disk imajı. Silindiğinde sanal cihaz verileri kaldırılır.",
        "dname_rustup": "Rust Araç Zinciri (.rustup)",
        "dnote_rustup": "Kurulu Rust derleyici sürümleri ve standart kitaplık hedefleri.",
        "dnote_jdk": "Java Geliştirme Kiti (JDK) dizini.",
        "dnote_active_runtime": "Etkin çalışma zamanı ortamı.",
        "dnote_scope_prefix": "Kapsam: {scope}",
    },
    "en": {
        # General / Units
        "unit_zero_bytes": "0 Bytes",
        "unit_bytes": "Bytes",
        "unknown": "Unknown",
        "unspecified": "Not specified",
        "ready": "Ready",
        "ok": "OK",
        "cancel": "Cancel",
        "yes": "Yes",
        "no": "No",
        "category_word": "Category",
        "active_tag": "[Active]",

        # Scope
        "scope_sys64": "System (64-bit)",
        "scope_sys32": "System (32-bit)",
        "scope_user": "Current User",

        # Window & Menus
        "app_subtitle": "Disk and Developer Management",
        "menu_file": "&File",
        "menu_refresh_view": "Refresh Active View",
        "menu_exit": "Exit",
        "menu_view": "&View",
        "menu_refresh_drives": "Refresh Disk Status",
        "menu_language": "&Language (Dil)",
        "menu_help": "&Help",
        "menu_about": "About DevClean",
        "lang_tr": "Türkçe",
        "lang_en": "English",
        "sidebar_sections": "Control Panel Sections",
        "sidebar_language": "Display Language",
        "sidebar_drives": "Fixed Disk Status",
        "nav_apps": "Installed Applications",
        "nav_caches": "Temporary Developer Files",
        "nav_devtools": "Development Tools & SDKs",

        # Drive Card
        "drive_title": "Local Disk ({drive})",
        "drive_sub": "{free} free of {total}",

        # About Dialog
        "about_title": "About DevClean",
        "about_html": (
            "<b>DevClean</b><br>"
            "Version 1.1<br><br>"
            "Developer Disk Cleanup, Installed Application, and SDK Management Utility.<br><br>"
            "• Review and uninstall installed applications consuming large amounts of disk space<br>"
            "• Clean temporary developer directories (<code>.venv</code>, <code>.cache</code>, <code>.nuget</code>, "
            "<code>__pycache__</code>, <code>node_modules</code>, <code>.gradle</code>)<br>"
            "• Manage Visual Studio, VS SDKs (.NET and Windows Kits), Python, PyCharm, and Android Studio"
        ),

        # Common Commands & Errors
        "btn_uninstall": "Uninstall",
        "btn_modify": "Change",
        "btn_modify_repair": "Change / Repair",
        "btn_open_location": "Open File Location",
        "btn_refresh": "Refresh",
        "err_no_uninstall_cmd": "No uninstall command is defined.",
        "err_invalid_uninstaller": "Could not resolve a valid uninstaller executable path.",
        "msg_uninstaller_started": "Official uninstaller launched.",
        "err_uninstaller_failed": "Failed to launch uninstaller: {error}",
        "err_elevated_win_only": "Elevated execution is only supported on Windows.",
        "err_uac_cancelled": "Could not start the uninstaller or administrator confirmation was cancelled.",
        "err_path_missing": "The specified path does not exist.",
        "err_protected_runtime": "The active Python runtime environment cannot be deleted for safety.",
        "msg_moved_to_recycle": "Moved to the Recycle Bin.",
        "err_recycle_failed": "Recycle Bin operation could not complete (Code: 0x{code:X}). Files may be in use.",
        "msg_deleted_perm": "Permanently deleted.",
        "err_delete_failed": "Deletion error: {error}",
        "msg_folder_not_found": "The specified directory was not found on disk.",

        # Tab 1: Installed Applications
        "apps_banner_title": "Installed Applications and Disk Usage",
        "apps_banner_sub": (
            "Sort applications by disk space consumption. "
            "To uninstall an application, select it from the list and click Uninstall."
        ),
        "apps_chk_calc_sizes": "Calculate missing sizes from disk",
        "apps_chk_calc_sizes_tip": (
            "Calculates installation folder size on disk for applications without size metadata in the Registry."
        ),
        "apps_lbl_size_filter": "Size:",
        "apps_filter_all": "All Sizes",
        "apps_filter_100mb": "100 MB and larger",
        "apps_filter_500mb": "500 MB and larger",
        "apps_filter_1gb": "1 GB and larger",
        "apps_filter_5gb": "5 GB and larger",
        "apps_search_ph": "Search application or publisher...",
        "apps_col_name": "Name",
        "apps_col_publisher": "Publisher",
        "apps_col_size": "Size",
        "apps_col_date": "Installed On",
        "apps_col_version": "Version",
        "apps_col_scope": "Scope",
        "apps_scanning": "Reading installed applications...",
        "apps_scanning_reg": "Reading installed applications from the Windows Registry...",
        "apps_calc_folder": "Calculating folder size: {name}",
        "apps_scan_done_status": "Listed {count} installed applications ({size}).",
        "apps_calculated_suffix": " (calculated from folder)",
        "apps_det_default_title": "Installed Applications",
        "apps_det_publisher": "Publisher: {val}",
        "apps_det_version": "Version: {val}",
        "apps_det_size": "Disk Size: {val}",
        "apps_det_location": "Location: {val}",
        "apps_sum_count": "Displayed Applications: {count}",
        "apps_sum_size": "Total Occupied Space: {size}",
        "apps_sum_sort_tip": "Sorting: Click any column header to change sort order",
        "apps_sum_unins_tip": "Note: Uninstalling launches the application's official uninstaller",
        "apps_confirm_title": "DevClean — Confirm Application Uninstall",
        "apps_confirm_body": (
            "Launch the official uninstaller to remove '{name}'?\n\n"
            "Publisher: {publisher}\n"
            "Estimated Size: {size}\n"
            "Command: {cmd}"
        ),
        "apps_unins_err_title": "DevClean — Unable to Start Uninstaller",
        "apps_mod_err_title": "DevClean — Unable to Start Setup",
        "apps_no_loc_msg": "No valid installation directory was found for this application.",

        # Tab 2: Temporary Developer Files
        "caches_banner_title": "Temporary Developer Files and Cache Cleanup",
        "caches_banner_sub": (
            "Inspect and safely clean virtual environments (.venv), package caches "
            "(.cache, .nuget, pip, npm, Gradle), and recreatable build outputs."
        ),
        "caches_btn_rescan": "Rescan",
        "caches_btn_roots": "Scanned Folders...",
        "caches_btn_recycle": "Move to Recycle Bin",
        "caches_btn_delete_perm": "Delete Permanently",
        "caches_btn_select_all": "Select All",
        "caches_btn_clear_sel": "Clear Selection",
        "caches_search_ph": "Search .venv, .cache, .nuget, or project...",
        "caches_sel_summary": "Selected space to clean: {size} ({count} items)",
        "caches_roots_hint": "Scanning global caches + {count} project directories",
        "caches_col_name": "Cache / Temporary Directory",
        "caches_col_size": "Size",
        "caches_col_files": "File Count",
        "caches_col_modified": "Last Modified",
        "caches_col_path": "Full Path",
        "caches_dirs_count": "{count} directories",
        "caches_scanning_status": "Scanning temporary developer files (.venv, .cache, .nuget, etc.)...",
        "caches_scan_global": "Scanning global cache: {name}",
        "caches_scan_dir": "Scanning directory: {path}",
        "caches_calc_size": "Calculating size: {path}",
        "caches_cleaning_item": "Cleaning: {path}",
        "caches_scan_done_status": "Scan completed: {count} temporary developer directories found ({size}).",
        "caches_det_default_title": "Temporary Developer Files",
        "caches_sum_total": "Total Discovered Caches: {size} ({count} folders)",
        "caches_sum_selected": "Selected Space to Reclaim: {size} ({count} folders)",
        "caches_sum_scope": "Scope: .venv, .cache, .nuget, __pycache__, node_modules, .gradle, pip, npm",
        "caches_sum_tip": "Tip: Use 'Move to Recycle Bin' for safe recovery if needed",
        "caches_cat_det_size": "Category Total Size: {size}",
        "caches_cat_det_files": "Total File Count: {count}",
        "caches_cat_det_dirs": "Subdirectory Count: {count}",
        "caches_cat_det_tip": "Toggle the category checkbox to select or clear all items in this group.",
        "caches_item_det_cat": "Category: {cat} ({group})",
        "caches_item_det_size": "Size: {size} ({files} files)",
        "caches_item_det_desc": "Description: {desc}",
        "caches_item_det_path": "Location: {path}",
        "caches_group_global": "Global Cache",
        "caches_group_project": "Project Directory",
        "caches_confirm_recycle_title": "Confirm Move to Recycle Bin",
        "caches_confirm_perm_title": "Confirm Permanent Deletion",
        "caches_confirm_recycle_desc": "Selected directories will be moved to the Windows Recycle Bin.",
        "caches_confirm_perm_desc": "Selected directories will be PERMANENTLY deleted from disk bypassing the Recycle Bin.",
        "caches_confirm_more": "... and {count} additional directories",
        "caches_confirm_body": (
            "{desc}\n\n"
            "Selected Directories: {count}\n"
            "Total Size: {size}\n\n"
            "{preview}\n\n"
            "Do you want to proceed?"
        ),
        "caches_done_title": "DevClean — Cleanup Completed",
        "caches_warn_title": "DevClean — Cleanup Summary",
        "caches_done_summary": (
            "Cleanup operation finished.\n\n"
            "Cleaned Directories: {count}\n"
            "Reclaimed Disk Space: {size}"
        ),
        "caches_done_skipped": "Some directories were skipped because files were in use:",
        "caches_done_more_err": "... ({count} additional errors)",

        # Scanned Folders Dialog
        "roots_dlg_title": "DevClean — Project Directories to Scan",
        "roots_dlg_info": (
            "Temporary developer directories (.venv, .cache, .nuget, __pycache__, node_modules, etc.) "
            "are searched within the following workspace folders:"
        ),
        "roots_btn_add": "Add Folder...",
        "roots_btn_remove": "Remove Selected",
        "roots_btn_reset": "Reset to Defaults",
        "roots_pick_title": "Select Project Directory",

        # Cache Categories & Descriptions
        "ccat_nuget": "NuGet Cache (.nuget)",
        "ccat_cache": "General Cache (.cache)",
        "ccat_py_venv": "Python Virtual Environment (.venv)",
        "ccat_py_cache": "Python Caches",
        "ccat_node_cache": "Node.js and Web Caches",
        "ccat_node_modules": "Node.js Dependencies (node_modules)",
        "ccat_gradle": "Gradle / Java / Android Caches",
        "ccat_rust_go": "Rust / Go Build Caches",
        "ccat_ide": "IDE Temporary Caches",
        "ccat_build_out": "Build Outputs (target / obj)",

        "cname_nuget_pkgs": "NuGet Global Package Cache (.nuget\\packages)",
        "cdesc_nuget_pkgs": "User cache of downloaded NuGet packages. Re-downloaded automatically during builds when needed.",
        "cname_nuget_v3": "NuGet HTTP v3 Cache",
        "cdesc_nuget_v3": "NuGet package feed metadata cache.",
        "cname_nuget_scratch": "NuGet Temporary Folder (NuGetScratch)",
        "cdesc_nuget_scratch": "Temporary extraction files created during NuGet operations.",
        "cname_user_cache": "User .cache Directory (~\\.cache)",
        "cdesc_user_cache": "Shared cache directory used by developer tools (pip, pre-commit, HuggingFace, Playwright, etc.).",
        "cname_pip_cache": "Pip Package Download Cache",
        "cdesc_pip_cache": "Local cache of .whl packages and source archives downloaded by pip.",
        "cname_uv_cache": "uv Package Manager Cache",
        "cdesc_uv_cache": "Wheel and archive cache used by the uv Python package manager.",
        "cname_poetry_cache": "Poetry Cache",
        "cdesc_poetry_cache": "Download cache used by the Poetry package manager.",
        "cname_npm_local": "npm Cache (Local)",
        "cdesc_npm_local": "npm package manager cached packages and metadata.",
        "cname_npm_roaming": "npm Cache (Roaming)",
        "cdesc_npm_roaming": "Legacy npm cache directory in Roaming AppData.",
        "cname_yarn_cache": "Yarn Cache",
        "cdesc_yarn_cache": "Yarn package manager local cache.",
        "cname_pnpm_cache": "pnpm Cache",
        "cdesc_pnpm_cache": "pnpm metadata and download cache.",
        "cname_gradle_caches": "Gradle Build Cache (~\\.gradle\\caches)",
        "cdesc_gradle_caches": "Shared Gradle dependency and build cache for Android Studio and Java projects.",
        "cname_gradle_daemon": "Gradle Daemon Logs (~\\.gradle\\daemon)",
        "cdesc_gradle_daemon": "Log files generated by background Gradle build daemons.",
        "cname_maven_repo": "Maven Local Repository (~\\.m2\\repository)",
        "cdesc_maven_repo": "Local archive of .jar dependencies downloaded by Apache Maven.",
        "cname_cargo_cache": "Cargo Registry Cache (~\\.cargo\\registry\\cache)",
        "cdesc_cargo_cache": "Compressed .crate archives downloaded by Rust Cargo.",
        "cname_go_build": "Go Build Cache (go-build)",
        "cdesc_go_build": "Incremental compilation cache used by the Go compiler.",
        "cname_vs_pkgs": "Visual Studio User Package Cache",
        "cdesc_vs_pkgs": "User-level temporary component cache for Visual Studio.",
        "cname_jb_caches": "JetBrains {ide} Index Cache",
        "cdesc_jb_caches": "{ide} indexing cache (rebuilt automatically on next IDE startup).",
        "cname_jb_logs": "JetBrains {ide} Log Files",
        "cdesc_jb_logs": "{ide} diagnostic and error log files.",
        "cdesc_ws_venv": "Python virtual environment directory (can be recreated from requirements.txt).",
        "cdesc_ws_cache": "Project-local temporary tool and compiler cache.",
        "cdesc_ws_nuget": "Project-local NuGet cache directory.",
        "cdesc_ws_pycache": "Python compiled bytecode / testing / linter cache ({folder}).",
        "cdesc_ws_nodemod": "Node.js project dependencies folder (recreatable via npm/pnpm/yarn install).",
        "cdesc_ws_vs": "Visual Studio solution IntelliSense and workspace cache (.vs).",
        "cdesc_ws_gradle": "Project-local Gradle build cache (.gradle).",
        "cdesc_ws_target": "Rust Cargo or Maven build output directory (target).",
        "cdesc_ws_obj": ".NET / MSBuild intermediate build artifacts directory (obj).",

        # Tab 3: Development Tools & SDKs
        "dev_banner_title": "Development Tools, Programming Languages, and SDK Management",
        "dev_banner_sub": (
            "Manage or uninstall Visual Studio, VS SDKs (.NET and Windows Kits), Python, PyCharm, "
            "and Android Studio installations and SDK components."
        ),
        "dev_btn_modify_workloads": "Modify / Workloads",
        "dev_btn_remove_folder": "Delete Component Folder",
        "dev_btn_remove_folder_tip": (
            "Removes SDK subcomponents without a separate Registry uninstaller "
            "(Android System Images, NDK, AVDs, leftover IDE data directories)."
        ),
        "dev_btn_vs_installer": "VS Installer",
        "dev_btn_vs_installer_tip": "Opens Microsoft Visual Studio Installer.",
        "dev_filter_all_cats": "All Categories",
        "dev_search_ph": "Search tool, language, or SDK...",
        "dev_col_name": "Component / Language / IDE",
        "dev_col_kind": "Type",
        "dev_col_version": "Version",
        "dev_col_size": "Size",
        "dev_col_location": "Installation Location",
        "dev_empty_category": "No installed components detected in this category",
        "dev_scanning_status": "Scanning development languages and SDK components...",
        "dev_scan_vs": "Checking Visual Studio installations...",
        "dev_scan_reg": "Scanning Registry for development tools and SDKs...",
        "dev_scan_sdks": "Scanning VS SDKs (.NET SDK and Windows Kits)...",
        "dev_scan_python": "Scanning Python distributions...",
        "dev_scan_pycharm": "Scanning PyCharm installations and data directories...",
        "dev_scan_android": "Scanning Android Studio, Android SDK, and emulator images...",
        "dev_scan_other": "Scanning additional programming languages and toolchains...",
        "dev_scan_done_status": "Development tools scan completed: {count} components ({size}).",
        "dev_det_default_title": "Development Tools and SDK Management",
        "dev_det_cat_kind": "Category: {cat} ({kind})",
        "dev_det_ver_pub": "Version: {ver} | Publisher: {pub}",
        "dev_det_size_note": "Size: {size} | Note: {note}",
        "dev_det_location": "Location: {loc}",
        "dev_sum_count": "Detected Development Components: {count}",
        "dev_sum_size": "Total Development Environment Size: {size}",
        "dev_sum_envs": "Managed Environments: Visual Studio, VS SDKs, Python, PyCharm, Android Studio",
        "dev_sum_tip": "Action: Select a component to run its official uninstaller or remove unused SDK directories",
        "dev_confirm_unins_title": "DevClean — Confirm Development Tool Uninstall",
        "dev_confirm_unins_body": (
            "Launch the official uninstaller to remove '{name}'?\n\n"
            "Category: {cat}\n"
            "Size: {size}\n"
            "Command: {cmd}"
        ),
        "dev_mod_err_title": "DevClean — Unable to Start Management Tool",
        "dev_del_folder_title": "DevClean — Confirm SDK / Data Folder Deletion",
        "dev_del_folder_q": "How would you like to delete the directory for '{name}'?",
        "dev_del_folder_info": "Location: {loc}\nSize: {size}\nDetails: {note}",
        "dev_del_err_title": "DevClean — Unable to Delete Directory",
        "dev_ctx_modify": "Modify / Manage Workloads",
        "dev_ctx_del_folder": "Delete Component Folder...",

        # DevTool Categories
        "dcat_vs": "Visual Studio",
        "dcat_vs_sdks": "VS SDKs (.NET and Windows Kits)",
        "dcat_python": "Python",
        "dcat_pycharm": "PyCharm",
        "dcat_android": "Android Studio and Android SDK",
        "dcat_other": "Other Development Languages and Tools",

        # DevTool Kinds
        "dkind_ide": "IDE",
        "dkind_ide_build": "IDE / Build Tools",
        "dkind_lang": "Programming Language",
        "dkind_sdk": "SDK / Development Kit",
        "dkind_sdk_sub": "SDK Subcomponent",
        "dkind_ide_data": "IDE Data Directory",
        "dkind_avd": "Emulator Virtual Device",
        "dkind_jdk": "JDK / Java",
        "dkind_vcs": "Version Control Tool",
        "dkind_build": "Build Tool",

        # DevTool Notes & Dynamic Names
        "dnote_vswhere": "Workloads can be modified or uninstalled via Visual Studio Installer.",
        "dnote_dotnet_sdk": "Shared .NET SDK directory. Uninstall via its MSI entry above or through Visual Studio Installer.",
        "dname_win_sdk_ver": "Windows 10/11 SDK Headers and Libraries ({ver})",
        "dnote_win_sdk_ver": "Include, Lib, and bin ({ver}) components under Windows Kits\\10.",
        "dname_win_kits10": "Windows Kits 10 Tools",
        "dnote_win_kits10": "Windows Kits 10 installation directory.",
        "dnote_py_active": "Active Python runtime environment (currently running DevClean).",
        "dnote_py_exe": "Interpreter path: {exe}",
        "dname_py_store": "Python {ver} (Microsoft Store Distribution)",
        "dnote_py_store": "Microsoft Store Appx package and user site-packages data.",
        "dname_py_active_interp": "Python {ver} (Active Interpreter)",
        "dnote_pycharm_user": "User-directory PyCharm installation.",
        "dname_pycharm_cache": "{folder} (Cache and Index Data)",
        "dnote_pycharm_cache": "PyCharm cache and index directory. Safe to remove if left over from an older version.",
        "dname_pycharm_cfg": "{folder} (Settings and Plugins)",
        "dnote_pycharm_cfg": "PyCharm settings and plugins directory. Safe to remove if left over from an older version.",
        "dnote_android_studio": "Android Studio IDE installation directory.",
        "dname_android_sysimg": "Android System Image — {ver}",
        "dname_android_ndk": "Android NDK — {ver}",
        "dname_android_plat": "Android Platform SDK — {ver}",
        "dname_android_bt": "Android Build-Tools — {ver}",
        "dnote_android_sub": "Android SDK ({folder}) component. Unused older API levels can be removed.",
        "dname_android_emu": "Android Emulator Engine",
        "dnote_android_emu": "Android SDK emulator runtime files.",
        "dname_android_avd": "Android Virtual Device (AVD): {name}",
        "dpub_user_avd": "User AVD",
        "dnote_android_avd": "Android emulator disk image. Deleting removes the virtual device data.",
        "dname_rustup": "Rust Toolchain (.rustup)",
        "dnote_rustup": "Installed Rust compiler toolchains and standard library targets.",
        "dnote_jdk": "Java Development Kit (JDK) directory.",
        "dnote_active_runtime": "Active runtime environment.",
        "dnote_scope_prefix": "Scope: {scope}",
    },
}


class I18nManager(QObject):
    """Uygulama genelinde çalışma zamanında dil değişimini yöneten sınıf."""

    language_changed = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings("DevClean", "DevClean")
        saved = str(self._settings.value("language", "tr") or "tr").lower()
        self._lang = saved if saved in ("tr", "en") else "tr"

    @property
    def language(self) -> str:
        return self._lang

    def set_language(self, lang_code: str) -> None:
        code = lang_code.lower()
        if code not in ("tr", "en") or code == self._lang:
            return
        self._lang = code
        self._settings.setValue("language", code)
        self.language_changed.emit(code)

    def t(self, key: str, **kwargs) -> str:
        table = TRANSLATIONS.get(self._lang, TRANSLATIONS["tr"])
        template = table.get(key) or TRANSLATIONS["tr"].get(key) or key
        if kwargs:
            try:
                return template.format(**kwargs)
            except (KeyError, ValueError):
                return template
        return template

    def format_int(self, number: int) -> str:
        sep = "." if self._lang == "tr" else ","
        return f"{number:,}".replace(",", sep)


i18n = I18nManager()


def tr(key: str, **kwargs) -> str:
    """Kısa çeviri erişim yardımcısı."""
    return i18n.t(key, **kwargs)
