from django.contrib import admin

from .models import MFAConfig, PasswordResetOTP


admin.site.register(PasswordResetOTP)
admin.site.register(MFAConfig)
