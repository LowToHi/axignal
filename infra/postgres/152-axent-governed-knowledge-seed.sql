CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Insert document authorities without a current revision first. The current-revision
-- foreign key is immediate, so the revision must exist before the pointer is set.
INSERT INTO axignal_global.knowledge_documents (
  knowledge_document_id,
  scope,
  tenant_id,
  document_type,
  slug,
  title,
  status,
  owner,
  current_revision_id
) VALUES (
  '4a1f2ae1-0000-4000-8000-000000000001',
  'GLOBAL',
  NULL,
  'SUPPORT_POLICY',
  'axent-support-boundaries',
  'Límites y autoridad de Axent',
  'ACTIVE',
  'AXIGNAL_SUPPORT_AUTHORITY',
  NULL
)
ON CONFLICT (knowledge_document_id) DO NOTHING;

INSERT INTO axignal_global.knowledge_revisions (
  revision_id,
  document_id,
  version,
  content,
  content_hash,
  effective_from,
  effective_until,
  reviewed_by,
  review_status,
  source_authority
) VALUES (
  '4a1f2ae1-0000-4000-8000-000000000101',
  '4a1f2ae1-0000-4000-8000-000000000001',
  1,
  'Axent puede explicar el estado de una cuenta, una suscripción, una investigación o un workspace mediante autoridades del servidor. Axent no modifica entitlements, no admite fuentes, no altera evidencia canónica y no sustituye decisiones legales, de privacidad ni operativas del cliente. Las acciones materiales requieren política, autoridad vigente y, cuando corresponda, confirmación explícita o intervención humana.',
  'sha256:' || encode(
    digest(
      'Axent puede explicar el estado de una cuenta, una suscripción, una investigación o un workspace mediante autoridades del servidor. Axent no modifica entitlements, no admite fuentes, no altera evidencia canónica y no sustituye decisiones legales, de privacidad ni operativas del cliente. Las acciones materiales requieren política, autoridad vigente y, cuando corresponda, confirmación explícita o intervención humana.',
      'sha256'
    ),
    'hex'
  ),
  '2026-08-03T00:00:00Z',
  NULL,
  'AXIGNAL_ENGINEERING_AUTHORITY',
  'APPROVED',
  'AX-CONTRACT-AXENT-SUPPORT-E2E-v1.0'
)
ON CONFLICT (revision_id) DO NOTHING;

INSERT INTO axignal_global.knowledge_chunks (
  chunk_id,
  revision_id,
  section_path,
  content,
  content_hash,
  language
) VALUES (
  '4a1f2ae1-0000-4000-8000-000000001001',
  '4a1f2ae1-0000-4000-8000-000000000101',
  'authority/boundaries',
  'Axent puede explicar estados verificados, proponer acciones permitidas y abrir casos. No puede modificar entitlements, admitir fuentes, alterar evidencia canónica ni aprobar decisiones legales, de privacidad o del cliente.',
  'sha256:' || encode(
    digest(
      'Axent puede explicar estados verificados, proponer acciones permitidas y abrir casos. No puede modificar entitlements, admitir fuentes, alterar evidencia canónica ni aprobar decisiones legales, de privacidad o del cliente.',
      'sha256'
    ),
    'hex'
  ),
  'es'
), (
  '4a1f2ae1-0000-4000-8000-000000001002',
  '4a1f2ae1-0000-4000-8000-000000000101',
  'actions/consent',
  'Las acciones materiales requieren autoridad vigente. Algunas exigen autenticación reforzada y una confirmación explícita vinculada al usuario, tenant, acción, parámetros, estado previo y caducidad.',
  'sha256:' || encode(
    digest(
      'Las acciones materiales requieren autoridad vigente. Algunas exigen autenticación reforzada y una confirmación explícita vinculada al usuario, tenant, acción, parámetros, estado previo y caducidad.',
      'sha256'
    ),
    'hex'
  ),
  'es'
)
ON CONFLICT (chunk_id) DO NOTHING;

UPDATE axignal_global.knowledge_documents
SET current_revision_id = '4a1f2ae1-0000-4000-8000-000000000101',
    updated_at = now()
WHERE knowledge_document_id = '4a1f2ae1-0000-4000-8000-000000000001'
  AND current_revision_id IS DISTINCT FROM
      '4a1f2ae1-0000-4000-8000-000000000101';

INSERT INTO axignal_global.knowledge_documents (
  knowledge_document_id,
  scope,
  tenant_id,
  document_type,
  slug,
  title,
  status,
  owner,
  current_revision_id
) VALUES (
  '4a1f2ae1-0000-4000-8000-000000000002',
  'GLOBAL',
  NULL,
  'BILLING_SUPPORT',
  'billing-authority-and-recovery',
  'Autoridad comercial, pagos y recuperación',
  'ACTIVE',
  'AXIGNAL_COMMERCIAL_AUTHORITY',
  NULL
)
ON CONFLICT (knowledge_document_id) DO NOTHING;

INSERT INTO axignal_global.knowledge_revisions (
  revision_id,
  document_id,
  version,
  content,
  content_hash,
  effective_from,
  effective_until,
  reviewed_by,
  review_status,
  source_authority
) VALUES (
  '4a1f2ae1-0000-4000-8000-000000000102',
  '4a1f2ae1-0000-4000-8000-000000000002',
  1,
  'El navegador y Axent no determinan el plan ni el entitlement. La autoridad comercial procede de eventos firmados del proveedor y de la reconciliación controlada. Un impago puede limitar capacidades según el estado persistido. Axent puede mostrar el estado verificado, explicar la recuperación disponible y escalar disputas o reembolsos a una autoridad humana.',
  'sha256:' || encode(
    digest(
      'El navegador y Axent no determinan el plan ni el entitlement. La autoridad comercial procede de eventos firmados del proveedor y de la reconciliación controlada. Un impago puede limitar capacidades según el estado persistido. Axent puede mostrar el estado verificado, explicar la recuperación disponible y escalar disputas o reembolsos a una autoridad humana.',
      'sha256'
    ),
    'hex'
  ),
  '2026-08-03T00:00:00Z',
  NULL,
  'AXIGNAL_ENGINEERING_AUTHORITY',
  'APPROVED',
  'AXIGNAL_COMMERCIAL_RUNTIME'
)
ON CONFLICT (revision_id) DO NOTHING;

INSERT INTO axignal_global.knowledge_chunks (
  chunk_id,
  revision_id,
  section_path,
  content,
  content_hash,
  language
) VALUES (
  '4a1f2ae1-0000-4000-8000-000000001003',
  '4a1f2ae1-0000-4000-8000-000000000102',
  'billing/authority',
  'El plan, la suscripción y los entitlements son autoridades del servidor. Solo los eventos firmados del proveedor y la reconciliación controlada pueden cambiar su estado.',
  'sha256:' || encode(
    digest(
      'El plan, la suscripción y los entitlements son autoridades del servidor. Solo los eventos firmados del proveedor y la reconciliación controlada pueden cambiar su estado.',
      'sha256'
    ),
    'hex'
  ),
  'es'
), (
  '4a1f2ae1-0000-4000-8000-000000001004',
  '4a1f2ae1-0000-4000-8000-000000000102',
  'billing/disputes',
  'Axent puede explicar estados de pago verificados. Las disputas de pago, reembolsos discrecionales y cambios manuales de entitlement requieren escalado humano.',
  'sha256:' || encode(
    digest(
      'Axent puede explicar estados de pago verificados. Las disputas de pago, reembolsos discrecionales y cambios manuales de entitlement requieren escalado humano.',
      'sha256'
    ),
    'hex'
  ),
  'es'
)
ON CONFLICT (chunk_id) DO NOTHING;

UPDATE axignal_global.knowledge_documents
SET current_revision_id = '4a1f2ae1-0000-4000-8000-000000000102',
    updated_at = now()
WHERE knowledge_document_id = '4a1f2ae1-0000-4000-8000-000000000002'
  AND current_revision_id IS DISTINCT FROM
      '4a1f2ae1-0000-4000-8000-000000000102';
