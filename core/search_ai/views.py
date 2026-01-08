from django.shortcuts import render
from django.db.models import Q
from items.models import Item
from .utils import parse_nl_query_to_filters
from datetime import datetime


def ai_search_view(request):
    ai_message = None
    result_items = []

    if request.method == "POST":
        query_text = request.POST.get("query", "").strip()

        if not query_text:
            ai_message = "Please enter what you're looking for."
            return render(request, "users/dashboard.html", {"ai_response": ai_message})

        # --------------------------------------------------------
        # RULE 1: Detect if the user is REALLY asking for a search
        # --------------------------------------------------------
        SEARCH_KEYWORDS = ["show", "find", "search", "look", "lost", "found", "locate", "where"]

        is_search = any(word in query_text.lower() for word in SEARCH_KEYWORDS)

        if not is_search:
            # Friendly assistant (NO SEARCH performed)
            ai_message = (
                "Hello! 😊\n"
                "I'm your Lost & Found Assistant.\n\n"
                "You can ask me things like:\n"
                "• 'Show all black backpacks found near the library'\n"
                "• 'Find lost iPhones from last week'\n"
                "• 'Search for a red water bottle found in the gym'\n"
            )
            return render(request, "users/dashboard.html", {"ai_response": ai_message})

        # --------------------------------------------------------
        # Step 1: Extract structured filters using LLM
        # --------------------------------------------------------
        filters = parse_nl_query_to_filters(query_text)

        # --------------------------------------------------------
        # Step 2: Start DB Query
        # --------------------------------------------------------
        items_qs = Item.objects.all().order_by("-date_reported")

        keyword = filters.get("keyword")
        category = filters.get("category")
        color = filters.get("color")
        location = filters.get("location")
        item_type = filters.get("item_type")
        start_date = filters.get("start_date")
        end_date = filters.get("end_date")

        # --------------------------------------------------------
        # Apply filters (improved)
        # --------------------------------------------------------

        if keyword:
            items_qs = items_qs.filter(item_name__icontains=keyword)

        if category:
            items_qs = items_qs.filter(category__icontains=category)

        if color:
            items_qs = items_qs.filter(color__icontains=color)

        if location:
            items_qs = items_qs.filter(location__icontains=location)

        # IMPORTANT FIX — only show lost OR found, not both
        if item_type:
            items_qs = items_qs.filter(item_type__iexact=item_type)

        # Parse dates safely
        def parse_date(value):
            if not value:
                return None
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return None

        start_d = parse_date(start_date)
        end_d = parse_date(end_date)

        if start_d:
            items_qs = items_qs.filter(date_lost_or_found__gte=start_d)
        if end_d:
            items_qs = items_qs.filter(date_lost_or_found__lte=end_d)

        result_items = list(items_qs)

        # --------------------------------------------------------
        # Step 3: Build FRIENDLY AI message
        # --------------------------------------------------------
        if len(result_items) == 0:
            ai_message = (
                "Sorry 😢\n"
                "We couldn't find any items matching your description."
            )
        else:
            ai_message = (
                f"Great news! 🎉\n"
                f"We found {len(result_items)} matching item(s):\n\n"
            )
            for item in result_items:
                ai_message += (
                    f"• {item.item_name}\n"
                    f"  Color: {item.color}\n"
                    f"  Location: {item.location or 'Not specified'}\n"
                    f"  Date: {item.date_lost_or_found}\n"
                    f"  Status: {item.item_type.capitalize()}\n\n"
                )

    # Return to dashboard with AI sidebar response
    return render(request, "users/dashboard.html", {
        "ai_response": ai_message,
        "ai_items": result_items,
    })
