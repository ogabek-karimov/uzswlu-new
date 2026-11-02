<script setup lang="ts">
import type { Post, PostType } from '#shared/types/api'

// Yangilik / e'lon / tadbir sahifasi (canvas: "Yangilik maqolasi")
const props = defineProps<{ type: PostType }>()

const { t, locale } = useI18n()
const route = useRoute()
const localePath = useLocalePath()
const formatDate = useFormatDate()
const requestUrl = useRequestURL()

const slug = computed(() => String(route.params.slug ?? ''))

const { data: post, error } = await useFetch<Post>(() => `/api/posts/${props.type}/${slug.value}`, { query: { lang: locale } })
if (error.value || !post.value) {
  throw createError({ statusCode: error.value?.statusCode ?? 404, statusMessage: 'Post not found', fatal: true })
}

const listLink = computed(() => (props.type === 'news' ? '/yangiliklar' : `/yangiliklar?type=${props.type}`))
const hasTime = computed(() => /T\d{2}:\d{2}/.test(post.value?.startsAt ?? ''))
// Sarlavha ostidagi vaqt: tadbirda — boshlanish, yangilik/e'londa — nashr vaqti (24 soatlik)
const headerAt = computed(() => post.value?.startsAt ?? post.value?.publishedAt ?? post.value?.date ?? '')
const headerHasTime = computed(() => /T\d{2}:\d{2}/.test(headerAt.value))
const initials = (name: string) => name.split(/\s+/).map(w => w[0]).join('').slice(0, 2).toUpperCase()

const pageUrl = computed(() => `${requestUrl.origin}${route.path}`)
const shareLinks = computed(() => [
  { label: t('posts.shareTelegram'), icon: 'simple-icons:telegram', href: `https://t.me/share/url?url=${encodeURIComponent(pageUrl.value)}&text=${encodeURIComponent(post.value?.title ?? '')}` },
  { label: t('posts.shareFacebook'), icon: 'simple-icons:facebook', href: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(pageUrl.value)}` },
])
const { copied, copy } = useShare()

useSeoMeta({
  title: () => post.value?.title ?? '',
  description: () => post.value?.excerpt ?? undefined,
  ogType: 'article',
  ogImage: () => post.value?.image ?? undefined,
})
</script>

<template>
  <div v-if="post">
    <article>
      <header class="mx-auto max-w-7xl px-4 pt-8 sm:px-6 lg:px-8">
        <PageBreadcrumbs :items="[{ label: t(`posts.tabs.${type}`), to: listLink }, { label: post.title }]" />
        <div class="mt-8 max-w-[920px]">
          <span class="rounded-full bg-brand-50 px-3 py-1.5 text-[13px] font-semibold text-brand-800">{{ post.category }}</span>
          <h1 class="mt-[18px] font-display text-[2.25rem] leading-[1.1] font-semibold tracking-tight text-ink sm:text-5xl lg:text-[52px]">{{ post.title }}</h1>
          <div class="mt-6 flex flex-wrap items-center gap-x-[18px] gap-y-3 text-sm text-muted">
            <span v-if="post.author" class="flex items-center gap-2.5">
              <img v-if="post.author.avatar" :src="post.author.avatar" alt="" class="size-10 rounded-full object-cover">
              <span v-else class="grid size-10 place-items-center rounded-full bg-brand-800 text-[13px] font-bold text-accent-400">{{ initials(post.author.name) }}</span>
              <span>
                <span class="block font-semibold text-ink">{{ post.author.name }}</span>
                {{ post.author.role }}
              </span>
            </span>
            <span v-if="post.author" class="hidden h-7 w-px bg-line sm:block" />
            <time :datetime="headerAt">{{ formatDate(headerAt) }}<template v-if="headerHasTime"> · {{ formatDate(headerAt, 'time') }}</template></time>
            <span>· {{ t('posts.minutes', { n: post.readingMinutes }) }}</span>
          </div>
        </div>

        <img v-if="post.image" :src="post.image" :alt="post.title" class="mt-9 aspect-[21/9] w-full rounded-[32px] object-cover">
        <div v-else class="decor relative mt-9 aspect-[21/9] overflow-hidden rounded-[32px] bg-brand-800" aria-hidden="true">
          <span class="absolute -right-[8%] -bottom-[60%] aspect-square w-[45%] rounded-full border-[3.5rem] border-white/5" />
          <span class="absolute top-1/2 left-[6%] -translate-y-1/2 font-display text-[clamp(4rem,12vw,10rem)] leading-none text-accent-400/90 italic">“</span>
        </div>
      </header>

      <div class="mx-auto flex max-w-7xl flex-col gap-10 px-4 pt-12 sm:px-6 lg:flex-row lg:items-start lg:gap-12 lg:px-8">
        <!-- Ulashish -->
        <aside :aria-label="t('page.share')" class="no-print flex gap-2.5 lg:sticky lg:top-36 lg:w-[52px] lg:shrink-0 lg:flex-col">
          <a v-for="link in shareLinks" :key="link.icon" :href="link.href" target="_blank" rel="noopener" :aria-label="link.label" :title="link.label" class="grid size-12 place-items-center rounded-full border border-line bg-white text-ink transition-colors hover:border-accent-500">
            <Icon :name="link.icon" class="size-[18px]" />
          </a>
          <button type="button" :aria-label="t('posts.copyLink')" :title="t('posts.copyLink')" class="relative grid size-12 place-items-center rounded-full border border-line bg-white text-ink transition-colors hover:border-accent-500" @click="copy(pageUrl)">
            <Icon :name="copied ? 'lucide:check' : 'lucide:link'" class="size-[18px]" />
            <span v-if="copied" role="status" class="absolute top-1/2 left-full ml-2 -translate-y-1/2 rounded-lg bg-ink px-2.5 py-1 text-xs whitespace-nowrap text-white">{{ t('page.copied') }}</span>
          </button>
        </aside>

        <div class="max-w-[720px] min-w-0 flex-1">
          <!-- Tadbir: vaqt va joy -->
          <dl v-if="type === 'events' && (post.startsAt || post.location)" class="mb-8 grid gap-4 rounded-3xl bg-brand-50 p-6 sm:grid-cols-2">
            <div v-if="post.startsAt">
              <dt class="text-[13px] text-muted">{{ t('posts.when') }}</dt>
              <dd class="mt-1 font-semibold">{{ formatDate(post.startsAt) }}<template v-if="hasTime">, {{ formatDate(post.startsAt, 'time') }}</template></dd>
            </div>
            <div v-if="post.location">
              <dt class="text-[13px] text-muted">{{ t('posts.where') }}</dt>
              <dd class="mt-1 font-semibold">{{ post.location }}</dd>
            </div>
          </dl>

          <ProseHtml :html="post.body" lead />
          <PostAttachments :items="post.attachments ?? []" />

          <div v-if="post.gallery.length" class="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-3">
            <img v-for="src in post.gallery" :key="src" :src="src" alt="" loading="lazy" class="aspect-[4/3] w-full rounded-[18px] object-cover">
          </div>

          <ul v-if="post.tags.length" class="mt-9 flex flex-wrap gap-2 border-t border-line pt-6 text-sm">
            <li v-for="tag in post.tags" :key="tag">
              <NuxtLink :to="{ path: localePath('/search'), query: { q: tag } }" class="inline-block rounded-full border border-line bg-white px-3.5 py-1.5 text-ink transition-colors hover:border-accent-500">#{{ tag }}</NuxtLink>
            </li>
          </ul>
        </div>

        <!-- So'nggi yangiliklar -->
        <aside v-if="post.latest.length" class="no-print w-full min-w-0 rounded-3xl border border-line bg-white p-6 lg:w-[340px] lg:shrink-0">
          <h2 class="text-lg font-semibold">{{ t('posts.latest') }}</h2>
          <ul class="mt-4 divide-y divide-line/70">
            <li v-for="item in post.latest" :key="item.id" class="py-3.5 first:pt-0 last:pb-0">
              <time :datetime="item.date" class="text-xs text-muted">{{ formatDate(item.date) }}</time>
              <NuxtLink :to="localePath(`/${item.type}/${item.slug}`)" class="mt-1 line-clamp-3 block text-[15px] leading-snug font-medium text-ink transition-colors hover:text-brand-700">{{ item.title }}</NuxtLink>
            </li>
          </ul>
          <NuxtLink :to="localePath('/yangiliklar')" class="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-brand-700">
            {{ t('posts.allNews') }}
            <Icon name="lucide:arrow-right" class="size-4" />
          </NuxtLink>
        </aside>
      </div>
    </article>

    <!-- O'xshash -->
    <section v-if="post.related.length" class="no-print mx-auto max-w-7xl px-4 pt-20 pb-24 sm:px-6 lg:px-8">
      <h2 class="font-display text-3xl font-semibold sm:text-4xl">{{ t('posts.related') }}</h2>
      <ul class="mt-7 grid gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-3">
        <li v-for="(item, i) in post.related" :key="item.id">
          <PostCard :item="item" :tone="i + 1" />
        </li>
      </ul>
    </section>
    <div v-else class="pb-24" />
  </div>
</template>
