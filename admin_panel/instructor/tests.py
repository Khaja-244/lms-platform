from django.test import SimpleTestCase
from django.urls import reverse


class InstructorPortalRouteTests(SimpleTestCase):
    def test_login_page(self):
        response = self.client.get(reverse("instructor:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Instructor Login")

    def test_dashboard_page(self):
        response = self.client.get(reverse("instructor:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mark attendance")
