import enum
from collections import OrderedDict
from typing import Dict

from lingua import Language


class Locale(enum.Enum):
    """Maps {language}_{country} to the name of the langage in said language."""

    en_GB = "English"
    af_ZA = "Afrikaans"
    an_ES = "Aragonés"
    ar_SA = "العربية"
    as_IN = "অসমীয়া"
    av_DA = "авар мацӀ"
    az_AZ = "Azərbaycanca"
    be_BY = "Беларуская"
    bg_BG = "български език"
    bn_BD = "বাংলা"
    br_FR = "Brezhoneg"
    bs_BA = "Bosanski"
    ca_ES = "Català, valencià"
    ckb_IR = "کوردی سۆرانی"
    co_FR = "Corsu"
    cs_CZ = "Čeština"
    cv_CU = "чӑваш чӗлхи"
    cy_GB = "Cymraeg"
    da_DK = "Dansk"
    de_DE = "Deutsch"
    el_GR = "Ελληνικά"
    en_US = "English (US)"
    eo_UY = "Esperanto"
    es_ES = "Español"
    et_EE = "Eesti keel"
    eu_ES = "Euskara"
    fa_IR = "فارسی"
    fi_FI = "Suomen kieli"
    fo_FO = "Føroyskt"
    fr_FR = "Français"
    frp_IT = "Arpitan"
    fy_NL = "Frysk"
    ga_IE = "Gaeilge"
    gd_GB = "Gàidhlig"
    gl_ES = "Galego"
    gsw_CH = "Schwizerdütsch"
    gu_IN = "ગુજરાતી"
    he_IL = "עִבְרִית"
    hi_IN = "हिन्दी, हिंदी"
    hr_HR = "Hrvatski"
    hu_HU = "Magyar"
    hy_AM = "Հայերեն"
    ia_IA = "Interlingua"
    id_ID = "Bahasa Indonesia"
    io_EN = "Ido"
    is_IS = "Íslenska"
    it_IT = "Italiano"
    ja_JP = "日本語"
    jbo_EN = "Lojban"
    jv_ID = "Basa Jawa"
    ka_GE = "ქართული"
    kab_DZ = "Taqvaylit"
    kk_KZ = "қазақша"
    kmr_TR = "Kurdî (Kurmancî)"
    kn_IN = "ಕನ್ನಡ"
    ko_KR = "한국어"
    ky_KG = "кыргызча"
    la_LA = "Lingua Latina"
    lb_LU = "Lëtzebuergesch"
    lt_LT = "Lietuvių kalba"
    lv_LV = "Latviešu valoda"
    mg_MG = "Fiteny malagasy"
    mk_MK = "македонски јази"
    ml_IN = "മലയാളം"
    mn_MN = "монгол"
    mr_IN = "मराठी"
    ms_MY = "Melayu"
    nb_NO = "Norsk bokmål"
    ne_NP = "नेपाली"
    nl_NL = "Nederlands"
    nn_NO = "Norsk nynorsk"
    pi_IN = "पालि"
    pl_PL = "Polski"
    ps_AF = "پښتو"
    pt_PT = "Português"
    pt_BR = "Português (BR)"
    ro_RO = "Română"
    ru_RU = "русский язык"
    ry_UA = "Русинська бисїда"
    sa_IN = "संस्कृत"
    sk_SK = "Slovenčina"
    sl_SI = "Slovenščina"
    sq_AL = "Shqip"
    sr_SP = "Српски језик"
    sv_SE = "Svenska"
    sw_KE = "Kiswahili"
    ta_IN = "தமிழ்"
    tg_TJ = "тоҷикӣ"
    th_TH = "ไทย"
    tk_TM = "Türkmençe"
    tl_PH = "Tagalog"
    tp_TP = "Toki pona"
    tr_TR = "Türkçe"
    uk_UA = "українська"
    ur_PK = "اُردُو"
    uz_UZ = "oʻzbekcha"
    vi_VN = "Tiếng Việt"
    yo_NG = "Yorùbá"
    zh_CN = "中文"
    zh_TW = "繁體中文"
    zu_ZA = "isiZulu"


def locale_to_str(loc: Locale) -> str:
    return loc.name.replace("_", "-")


# Uses the name of the language (in said language) as the key.
native_to_locale: OrderedDict[str, Locale] = OrderedDict(
    [(loc.value, loc) for loc in Locale]
)

# Uses an inferred/detected language as the key. Mapping was manually created
# using https://github.com/pemistahl/lingua-rs/blob/main/src/isocode.rs#L40 as
# a reference.
lang_to_locale: Dict[Language, Locale] = {
    Language.CHINESE: Locale.zh_CN,
    Language.CROATIAN: Locale.hr_HR,
    Language.DANISH: Locale.da_DK,
    Language.DUTCH: Locale.nl_NL,
    Language.ENGLISH: Locale.en_GB,
    Language.FINNISH: Locale.fi_FI,
    Language.FRENCH: Locale.fr_FR,
    Language.GERMAN: Locale.de_DE,
    Language.HUNGARIAN: Locale.hu_HU,
    Language.ITALIAN: Locale.it_IT,
    Language.KOREAN: Locale.ko_KR,
    Language.LATIN: Locale.la_LA,
    Language.MALAY: Locale.ms_MY,
    Language.PERSIAN: Locale.fa_IR,
    Language.POLISH: Locale.pl_PL,
    Language.PORTUGUESE: Locale.pt_PT,
    Language.ROMANIAN: Locale.ro_RO,
    Language.RUSSIAN: Locale.ru_RU,
    Language.SLOVENE: Locale.sl_SI,
    Language.SPANISH: Locale.es_ES,
    Language.SWAHILI: Locale.sw_KE,
    Language.SWEDISH: Locale.sv_SE,
    Language.TAGALOG: Locale.tl_PH,
    Language.TURKISH: Locale.tr_TR,
    Language.UKRAINIAN: Locale.uk_UA,
    Language.VIETNAMESE: Locale.vi_VN,
    Language.YORUBA: Locale.yo_NG,
}
