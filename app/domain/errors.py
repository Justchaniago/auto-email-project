class AutoEmailError(Exception):
    code = 'auto_email_error'; safe_message = 'The request could not be completed.'; http_status = 500
class ConfigurationError(AutoEmailError):
    code = 'configuration_error'; safe_message = 'Service configuration is invalid.'
class UnsupportedStoreError(AutoEmailError):
    code = 'unsupported_store'; safe_message = 'Unsupported store code.'; http_status = 400
class CredentialUnavailableError(AutoEmailError):
    code = 'credential_unavailable'; safe_message = 'Gmail credentials are unavailable.'
class CredentialRefreshError(AutoEmailError):
    code = 'credential_refresh_failed'; safe_message = 'Gmail credentials could not be refreshed.'
class RunConflictError(AutoEmailError):
    code = 'run_in_progress'; safe_message = 'An equivalent run is already processing.'; http_status = 409
class EffectUncertainError(AutoEmailError):
    code = 'effect_uncertain'; safe_message = 'Gmail effect could not be confirmed; reconciliation is required.'
class PersistenceUnavailableError(AutoEmailError):
    code = 'persistence_unavailable'; safe_message = 'Run state is temporarily unavailable.'
class GmailOperationError(AutoEmailError):
    code = 'gmail_operation_failed'; safe_message = 'Gmail draft creation failed.'
