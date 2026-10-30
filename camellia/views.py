from django.shortcuts import render
from django.http import HttpResponse


def home(request):
    return HttpResponse(
        "<h1>Welcome to Camellia Restaurant</h1>"
        "<p>Experience fine dining, artisanal flavors, and seasonal delicacies.</p>"
    )

def reservation(request):
    return HttpResponse(
        "<h1>Table Reservations - Camellia</h1>"
        "<p>Reserve your table for lunch or dinner. Call us at +1 (555) 019-2834 or book online.</p>"
    )

















# def menu(request):
#     return HttpResponse(
#         "<h1>Camellia Restaurant - Menu</h1>"
#         "<ul>"
#         "<li><strong>Appetizers:</strong> Truffle Bruschetta, Wild Mushroom Tart</li>"
#         "<li><strong>Entrees:</strong> Pan-Seared Salmon, Ribeye Steak, Herb Roasted Chicken</li>"
#         "<li><strong>Desserts:</strong> Camellia Signature Tiramisu, Lava Cake</li>"
#         "<li><strong>Beverages:</strong> Artisanal Cocktails, Vintage Wine Selection</li>"
#         "</ul>"
#     )

# def contact(request):
#     return HttpResponse(
#         "<h1>Contact & Location - Kacyiru</h1>"
#         "<p><strong>Address:</strong> KK 893 Street</p>"
#         "<p><strong>Hours:</strong> Mon - Sun: 11:00 AM - 11:00 PM</p>"
#         "<p><strong>Email:</strong> reservations@camelliarestaurant.com</p>"
#     )