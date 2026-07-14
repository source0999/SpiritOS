import "server-only";

/**
 * Administrative mutations have no ordinary-session fallback.  This boundary
 * deliberately fails closed until a persisted SpiritFlix admin preview has
 * been issued and consumed by the shared Approval Authority.
 */
export const SPIRITFLIX_ADMIN_DIRECT_MUTATION_FORBIDDEN = "spiritflix_admin_direct_mutation_forbidden";

export function spiritFlixAdminMutationDenied() {
  return { reason_code: SPIRITFLIX_ADMIN_DIRECT_MUTATION_FORBIDDEN };
}
