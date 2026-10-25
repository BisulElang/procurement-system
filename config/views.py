from django.contrib.auth.views import LoginView
from django.urls import reverse


class RoleBasedLoginView(LoginView):
    template_name = "registration/login.html"

    def get_success_url(self):
        role = self.request.user.role

        if role == "APPROVER":
            return reverse("requisitions:approval_list")

        if role == "REQUESTER":
            return reverse("requisitions:pr_list")

        if role == "PROCUREMENT_OFFICER":
            return reverse("requisitions:procurement_pr_list")

        if role == "PROCUREMENT_MANAGER":
            return reverse("requisitions:manager_dashboard")
        
        return reverse("requisitions:pr_list")
