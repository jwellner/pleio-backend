from django.http import JsonResponse

def index(request):
    return JsonResponse({
        'app': 'backend2',
        'status': 200,
        'description': 'Backend2 is working correctly. Visit /graphql/ for the GraphQL API, visit /oidc/authenticate/ for login, visit /admin/ for the admin panel.'
    })
