from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class NoSignupAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return True