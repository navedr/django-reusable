from enum import Enum


class Umoor(Enum):
    Deeniyah = 'Deeniyah'
    Talimiyah = 'Talimiyah'
    Marafiq_Burhaniyah = 'Marafiq Burhaniyah'
    Maliyah = 'Maliyah'
    Mawarid_Bashariyah = 'Mawarid Bashariyah'
    Dakheliyah = 'Dakheliyah'
    Kharejiyah = 'Kharejiyah'
    Iqtesadiyah = 'Iqtesadiyah'
    Faizul_Mawaid_il_Burhaniyah = 'Faizul Mawaid il Burhaniyah'
    al_Qaza = 'al-Qaza'
    al_Amlaak = 'al-Amlaak'
    al_Sehhat = 'al-Sehhat'


UMOOR_ACCOUNT_NUMBERS = {
    Umoor.Maliyah: '4010',
    Umoor.Faizul_Mawaid_il_Burhaniyah: '4016',
    Umoor.Talimiyah: '4015',
}

UMOOR_FRIENDLY_NAMES = {
    Umoor.Talimiyah.value: 'Madrasah',
    Umoor.Faizul_Mawaid_il_Burhaniyah.value: 'FMB',
    Umoor.Maliyah.value: 'Sabil ul-Khair wal-Barakat'
}

YEARLY_RECEIPT_ACCOUNTS = ['4010', '4014', '4015.52', '4016.1', '4016.2', '4016.3', '4016.4', '4016.5', '4017',
                           '4017.1', '4017.3', '4025.1', '4025.9', '4029', '4031', '4034', '4035', '4036']
