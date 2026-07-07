// MSAL configuration for advisor sign-in (Microsoft Entra ID).
//
// The signed-in user must have access to both the Foundry project and the Fabric
// workspace/Data Agent. Their delegated Azure AI Search token is sent to the
// backend and used as `x-ms-query-source-authorization`, which the search service
// exchanges (OBO) to call the Fabric Data Agent knowledge source.
import type { Configuration, PopupRequest, SilentRequest } from '@azure/msal-browser'

const clientId =
  (import.meta.env.VITE_AAD_CLIENT_ID as string | undefined) ??
  'e16291f8-52df-408d-9373-90d53fae489d'
const tenantId =
  (import.meta.env.VITE_AAD_TENANT_ID as string | undefined) ??
  'ee0398ee-3d71-481a-948e-8c2e4c7aacf7'

export const msalConfig: Configuration = {
  auth: {
    clientId,
    authority: `https://login.microsoftonline.com/${tenantId}`,
    redirectUri: window.location.origin,
    postLogoutRedirectUri: window.location.origin,
  },
  cache: {
    cacheLocation: 'sessionStorage',
    storeAuthStateInCookie: false,
  },
}

// Interactive sign-in scope (basic profile).
export const loginRequest: PopupRequest = {
  scopes: ['User.Read'],
}

// Delegated Azure AI Search scope. This token is the OBO subject for the
// Fabric Data Agent knowledge source.
export const searchRequest: SilentRequest = {
  scopes: ['https://search.azure.com/user_impersonation'],
}
