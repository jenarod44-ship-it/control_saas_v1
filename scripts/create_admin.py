from django.contrib.auth import get_user_model

User = get_user_model()

user, created = User.objects.get_or_create(
    username="admin",
    defaults={
        "email": "admin@admin.com",
        "is_staff": True,
        "is_superuser": True,
    }
)

user.set_password("admin123")
user.is_staff = True
user.is_superuser = True
user.email = "admin@admin.com"
user.save()

print("Administrador listo.")