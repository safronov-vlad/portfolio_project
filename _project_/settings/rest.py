REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'core.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
        'rest_framework.permissions.IsAdminUser'
    ),
    'TEST_REQUEST_RENDERER_CLASSES': (
        # NOTE: Do not remove this comma, as it might turn this tuple into a string
        'rest_framework.renderers.JSONRenderer',
    )
}
