import { APIError, type CollectionConfig } from 'payload'
import { isSuper, superOnly, superOrSelf } from '../lib/access'
import { logActivity } from '../lib/activity'
import { requestInfo } from '../lib/request'

// Adminlar. Superadmin login-parol bilan kiradi; muharrirlar keyinchalik HEMIS orqali ham kiradi.
export const Users: CollectionConfig = {
  slug: 'users',
  labels: { singular: 'Foydalanuvçi', plural: 'Foydalanuvçilar' },
  admin: { useAsTitle: 'name', defaultColumns: ['name', 'username', 'role', 'status'] },
  auth: {
    loginWithUsername: { allowEmailLogin: true, requireEmail: false },
    // 5 ta xato urinishdan keyin hisob 15 daqiqaga bloklanadi
    maxLoginAttempts: 5,
    lockTime: 15 * 60 * 1000,
    tokenExpiration: 60 * 60 * 12,
    cookies: { sameSite: 'Lax', secure: process.env.NODE_ENV === 'production' && process.env.COOKIE_SECURE !== 'false' },
  },
  access: {
    read: superOrSelf,
    create: superOnly,
    update: superOrSelf,
    delete: superOnly,
    // Payload'ning o'z admin paneli faqat superadmin uchun (zaxira)
    admin: ({ req }) => isSuper(req.user as { role?: string }),
  },
  fields: [
    { name: 'name', label: 'F.I.Ş.', type: 'text', required: true },
    {
      name: 'role',
      label: 'Rol',
      type: 'select',
      required: true,
      defaultValue: 'editor',
      options: [
        { label: 'Superadmin', value: 'superadmin' },
        { label: 'Kontent muharriri', value: 'editor' },
        { label: 'Fakultet admini', value: 'faculty' },
        { label: 'Sahifalar muharriri', value: 'pages' },
        // Faqat BRM bo'limi: 17 maqsad matni, rasmlari va PDF hisobotlari
        { label: 'BRM menejeri', value: 'sdg' },
      ],
      access: { update: ({ req }) => isSuper(req.user as { role?: string }) },
    },
    {
      name: 'status',
      label: 'Holati',
      type: 'select',
      defaultValue: 'active',
      options: [
        { label: 'Faol', value: 'active' },
        { label: 'Taklif qilingan', value: 'invited' },
        { label: 'Yopilgan', value: 'disabled' },
      ],
      access: { update: ({ req }) => isSuper(req.user as { role?: string }) },
    },
    { name: 'position', label: 'Lavozim', type: 'text' },
    { name: 'department', label: 'Bölim', type: 'text' },
    { name: 'scope', label: 'Ruxsat doirasi (fakultet)', type: 'text' },
    { name: 'hemisId', label: 'HEMIS ID', type: 'text', index: true },
    { name: 'avatar', label: 'Rasm', type: 'upload', relationTo: 'media' },
  ],
  hooks: {
    beforeLogin: [
      ({ user }) => {
        if ((user as { status?: string }).status === 'disabled') throw new APIError('Hisob yopilgan', 403)
        return user
      },
    ],
    afterLogin: [
      async ({ req, user }) => {
        try {
          // req — login tranzaksiyasining o'zida (aks holda users qatori qulfida kutib qoladi)
          await req.payload.create({
            collection: 'login-events',
            overrideAccess: true,
            req,
            data: {
              user: user.id as number,
              username: (user as { username?: string }).username ?? (user as { email?: string }).email ?? '',
              method: 'password',
              result: 'success',
              ...requestInfo(req),
            },
          })
        }
        catch (error) {
          req.payload.logger.error({ err: error, msg: 'login event failed' })
        }
      },
    ],
    afterChange: [
      async ({ req, doc, previousDoc, operation }) => {
        if (operation === 'create') {
          await logActivity(req, { action: 'role', entity: 'users', entityId: doc.id, label: `${doc.name} — yangi admin (${doc.role})` })
        }
        else if (previousDoc && (previousDoc.role !== doc.role || previousDoc.status !== doc.status)) {
          await logActivity(req, {
            action: 'role',
            entity: 'users',
            entityId: doc.id,
            label: doc.name,
            changes: { role: { before: previousDoc.role, after: doc.role }, status: { before: previousDoc.status, after: doc.status } },
          })
        }
      },
    ],
  },
}
