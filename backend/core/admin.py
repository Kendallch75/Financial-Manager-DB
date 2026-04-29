from django.contrib import admin
from .models import User, Category, Account, Service, ExchangeRate, Movement, AccountLimit

admin.site.register(User)
admin.site.register(Category)
admin.site.register(Account)
admin.site.register(Service)
admin.site.register(ExchangeRate)
admin.site.register(Movement)
admin.site.register(AccountLimit)
