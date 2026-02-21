from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.http import require_POST, require_http_methods
from django.utils.timezone import now
from django.conf import settings
from django.db.models import Count
from django.db.models.functions import TruncDate

from .models import UserProfile, Prediction
from .ml.loader import predict_one, load_bundle


# ================= COMMON STAFF DECORATOR =================

def staff_required(view_func):
    return login_required(login_url="admin_login")(
        user_passes_test(lambda u: u.is_staff)(view_func)
    )


def is_admin(user):
    return user.is_staff


# ================= HOME =================

def home(request):
    return render(request, "home.html")


# ================= SIGNUP =================

@require_http_methods(["GET", "POST"])
def signup_view(request):
    if request.method == "POST":
        name = request.POST.get("full_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        terms = request.POST.get("terms")

        if not all([name, phone, email, password, confirm_password]):
            messages.error(request, "All fields are required.")
            return redirect("signup")

        if not phone.isdigit() or len(phone) != 10:
            messages.error(request, "Phone must be 10 digits.")
            return redirect("signup")

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
            return redirect("signup")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")

        if not terms:
            messages.error(request, "You must accept terms.")
            return redirect("signup")

        if User.objects.filter(username=email).exists():
            messages.error(request, "Account already exists.")
            return redirect("signup")

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        name_parts = name.split()
        user.first_name = name_parts[0]
        user.last_name = " ".join(name_parts[1:])
        user.save()

        UserProfile.objects.create(user=user, phone=phone)

        auth_login(request, user)
        return redirect(settings.LOGIN_REDIRECT_URL)

    return render(request, "signup.html")


# ================= LOGIN =================

@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        user = authenticate(request, username=email, password=password)

        if user:
            auth_login(request, user)
            return redirect(settings.LOGIN_REDIRECT_URL)

        messages.error(request, "Invalid credentials.")
        return redirect("login")

    return render(request, "login.html")


# ================= LOGOUT =================

@login_required
def logout_view(request):
    auth_logout(request)
    return redirect("login")


# ================= PREDICT =================

@login_required
def predict_view(request):
    bundle = load_bundle()
    feature_order = bundle["feature_cols"]

    result = None
    last_data = {}

    if request.method == "POST":
        try:
            input_data = []

            for feature in feature_order:
                value = request.POST.get(feature, "").strip()
                if not value:
                    messages.error(request, f"{feature} is required.")
                    return redirect("predict")

                numeric_value = float(value)
                input_data.append(numeric_value)
                last_data[feature] = numeric_value

            result = predict_one(input_data)

            Prediction.objects.create(
                user=request.user,
                predicted_label=result,
                **last_data
            )

        except ValueError:
            messages.error(request, "Invalid numeric input.")
        except Exception:
            messages.error(request, "Prediction failed. Please try again.")

    return render(request, "predict.html", {
        "feature_order": feature_order,
        "result": result,
        "last_data": last_data
    })


# ================= USER HISTORY =================

@login_required
def user_history_view(request):
    predictions = Prediction.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(request, "history.html", {
        "predictions": predictions
    })


@login_required
@require_http_methods(["POST"])
def user_delete_predictions(request, pk):
    prediction = get_object_or_404(
        Prediction,
        pk=pk,
        user=request.user
    )
    prediction.delete()
    return redirect("user_history")


# ================= PROFILE =================

@login_required
def user_profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        request.user.first_name = request.POST.get("first_name", "").strip()
        request.user.last_name = request.POST.get("last_name", "").strip()
        request.user.save()

        profile.phone = request.POST.get("phone", "").strip()
        profile.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("profile")

    total_predictions = Prediction.objects.filter(
        user=request.user
    ).count()

    return render(request, "profile.html", {
        "profile": profile,
        "total_predictions": total_predictions
    })


# ================= CHANGE PASSWORD =================

@login_required
def user_change_password_view(request):
    form = PasswordChangeForm(request.user, request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Password changed successfully.")
        return redirect("profile")

    return render(request, "change_password.html", {"form": form})


# ================= ADMIN LOGIN =================

@require_http_methods(["GET", "POST"])
def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("admin_dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if user and user.is_staff:
            auth_login(request, user)
            return redirect("admin_dashboard")

        messages.error(request, "Invalid admin credentials.")
        return redirect("admin_login")

    return render(request, "admin_login.html")


# ================= ADMIN DASHBOARD =================

@staff_required
def admin_dashboard_view(request):
    today = now().date()
    last_7_days = now() - timedelta(days=7)

    weekly_data = (
        Prediction.objects
        .filter(created_at__gte=last_7_days)
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    return render(request, "admin_dashboard.html", {
        "total_users": User.objects.count(),
        "active_users": User.objects.filter(is_active=True).count(),
        "total_predictions": Prediction.objects.count(),
        "today_predictions": Prediction.objects.filter(
            created_at__date=today
        ).count(),
        "weekly_data": list(weekly_data),
        "recent_predictions": Prediction.objects.select_related("user")
            .order_by("-created_at")[:10]
    })


# ================= ADMIN LOGOUT =================

@staff_required
def admin_logout_view(request):
    auth_logout(request)
    return redirect("home")


# ================= ADMIN VIEW PREDICTIONS =================

@staff_required
def admin_view_predictions(request):
    predictions = Prediction.objects.select_related(
        "user"
    ).order_by("-created_at")

    return render(request, "admin_view_predictions.html", {
        "predictions": predictions
    })


@staff_required
@require_http_methods(["POST"])
def admin_delete_prediction(request, pk):
    prediction = get_object_or_404(Prediction, pk=pk)
    prediction.delete()
    return redirect("admin_predictions")


# ================= ADMIN VIEW USERS =================

@staff_required
def admin_view_users(request):
    users = User.objects.order_by("-date_joined")
    return render(request, "admin_view_users.html", {
        "users": users
    })


@staff_required
@require_http_methods(["POST"])
def admin_delete_user(request, pk):
    user = get_object_or_404(User, pk=pk)

    if user.is_superuser or user.is_staff:
        messages.error(request, "Admin/Superuser cannot be deleted.")
    else:
        user.delete()
        messages.success(request, "User deleted successfully.")

    return redirect("admin_users")
# ===== Admin - View All Predictions =====
@login_required
@user_passes_test(is_admin)
def admin_predictions(request):

    predictions = (
        Prediction.objects
        .select_related("user")
        .order_by("-created_at")
    )

    return render(request, "admin_predictions.html", {
        "predictions": predictions
    })


# ===== Admin - Delete Prediction =====
@login_required
@user_passes_test(is_admin)
@require_POST
def admin_delete_prediction(request, pk):

    prediction = get_object_or_404(Prediction, id=pk)
    prediction.delete()

    messages.success(request, "Prediction deleted successfully.")

    return redirect("admin_predictions")