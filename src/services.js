import ApiClient from 'util/api-client';
import organization from "./reducers/organization";

export const requestLoginUser = (email, password) => ApiClient.post('/users/auth', {
  email,
  password,
});

export const requestRefreshJWT = () => ApiClient.post('/users/auth/refresh');

export const requestPasswordReset = (email) => ApiClient.post('/users/auth/reset', {
  email,
});

export const requestUpdatePassword = (email, reset_token, password) => (
  ApiClient.put('/users/auth/update-password', {
    email,
    reset_token,
    password,
  })
);

export const requestUserProfile = (user_uuid) => ApiClient.get(`/users/${user_uuid}/profile`);

export const requestOrganizationMembers = (organization_uuid) => (
  ApiClient.get(`/organizations/${organization_uuid}/members`)
);

export const requestRemoveOrganizationMember = (organization_uuid, user_uuid) => (
  ApiClient.delete(`/organizations/${organization_uuid}/members/${user_uuid}`)
);

export const requestChangeOrganizationMemberRole = (organization_uuid, user_uuid, role) => (
  ApiClient.post(`/organizations/${organization_uuid}/members/${user_uuid}/role`, { role })
);
