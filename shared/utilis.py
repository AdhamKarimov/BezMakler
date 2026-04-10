import re
from rest_framework.exceptions import ValidationError


email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
phone_regex = re.compile(r'^998([378]{2}|(9[013-57-9]))\d{7}$')
username_regex = re.compile(r'^[a-zA-Z][a-zA-Z0-9]{5,}$')
def check_email_or_phone(user_input):
    if not isinstance(user_input, str) or not user_input.strip():
        raise ValidationError("Email yoki telefon kiritilmadi")

    user_input = user_input.strip()

    if re.fullmatch(phone_regex, user_input):
        return 'phone'

    elif re.fullmatch(email_regex, user_input):
        return 'email'

    raise ValidationError("Email yoki telefon noto‘g‘ri formatda")



def check_email_or_phone_or_username(user_input):
    if not isinstance(user_input, str) or not user_input.strip():
        raise ValidationError("Email yoki telefon kiritilmadi")

    user_input = user_input.strip()

    if re.fullmatch(phone_regex, user_input):
        return 'phone'

    elif re.fullmatch(email_regex, user_input):
        return 'email'
    elif re.fullmatch(username_regex, user_input):
        return 'username'

    raise ValidationError("Login yki parol xato")