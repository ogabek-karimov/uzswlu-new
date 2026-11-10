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
// Telegram — alohida komponent (o'zbekcha surat + 4 tildagi havola)
const shareLinks = computed(() => [
  { label: t('posts.shareFacebook'), icon: 'simple-icons:facebook', href: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(pageUrl.value)}` },
])
const { copied, copy } = useShare()

// Asosiy surat kesilmaydi: asosiy ustun kengligida, o'z nisbatida (tik ham, yotiq ham — eski saytdagidek).
// Nisbat serverdan keladi (joy oldindan ajratiladi, sahifa sakramaydi); brauzer o'lchagani ustun (EXIF burilishi ham hisobga olinadi)
const coverImg = ref<HTMLImageElement>()
const measured = ref<number | null>(null)
const ratio = computed(() => measured.value ?? (post.value?.imageWidth && post.value.imageHeight ? post.value.imageWidth / post.value.imageHeight : null))
// Juda baland surat (masalan, telefon skrinshoti) 1100px dan oshmaydi
const coverStyle = computed(() => (ratio.value === null ? undefined : { aspectRatio: String(ratio.value), maxWidth: `calc(1100px * ${ratio.value})` }))
function measure() {
  const img = coverImg.value
  if (img?.naturalWidth && img.naturalHeight) measured.value = img.naturalWidth / img.naturalHeight
}
onMounted(() => coverImg.value?.complete && measure())

// To'liq ekranda ko'rish: asosiy surat va galereya bitta ro'yxatda
const viewerImages = computed(() => (post.value ? [...(post.value.image ? [post.value.image] : []), ...post.value.gallery] : []))
const galleryOffset = computed(() => (post.value?.image ? 1 : 0))
const viewerIndex = ref<number | null>(null)

useSeo({
  title: () => post.value?.title ?? '',
  description: () => post.value?.excerpt ?? undefined,
  type: 'article',
  image: () => post.value?.image,
})
</script>

<template>
  <div v-if="post">
    <article>
      <header class="mx-auto max-w-7xl px-4 pt-8 sm:px-6 lg:px-8">
        <PageBreadcrumbs :items="[{ label: t(`posts.tabs.${type}`), to: listLink }, { label: post.title }]" />
        <div class="mt-8 max-w-[920px]">
          <span v-if="post.category" class="mb-3 inline-block rounded-full bg-brand-50 px-3 py-1.5 text-[13px] font-semibold text-brand-800">{{ post.category }}</span>
          <h1 class="font-display text-[2.25rem] leading-[1.1] font-semibold tracking-tight text-ink sm:text-5xl lg:text-[52px]">{{ post.title }}</h1>
        </div>

        <!-- Muallif, sana va ulashish bir qatorda -->
        <div class="mt-6 flex flex-wrap items-center gap-x-[18px] gap-y-3 text-sm text-muted">
          <span v-if="post.author" class="flex items-center gap-2.5">
            <img v-if="post.author.avatar" :src="post.author.avatar" alt="" width="40" height="40" loading="lazy" class="size-10 rounded-full object-cover">
            <span v-else class="grid size-10 place-items-center rounded-full bg-brand-800 text-[13px] font-bold text-accent-400">{{ initials(post.author.name) }}</span>
            <span>
              <span class="block font-semibold text-ink">{{ post.author.name }}</span>
              {{ post.author.role }}
            </span>
          </span>
          <span v-if="post.author" class="hidden h-7 w-px bg-line sm:block" />
          <time :datetime="headerAt">{{ formatDate(headerAt) }}<template v-if="headerHasTime"> · {{ formatDate(headerAt, 'time') }}</template></time>
          <span>· {{ t('posts.minutes', { n: post.readingMinutes }) }}</span>

          <div role="group" :aria-label="t('page.share')" class="no-print flex items-center gap-2 sm:ml-auto">
            <span class="mr-1 text-[13px]">{{ t('page.share') }}</span>
            <TelegramShare :type="type" :slug="slug" :translations="post.translations" :image="post.image" />
            <a v-for="link in shareLinks" :key="link.icon" :href="link.href" target="_blank" rel="noopener" :aria-label="link.label" :title="link.label" class="grid size-10 place-items-center rounded-full border border-line bg-white text-ink transition-colors hover:border-accent-500">
              <Icon :name="link.icon" class="size-4" />
            </a>
            <button type="button" :aria-label="t('posts.copyLink')" :title="t('posts.copyLink')" class="relative grid size-10 place-items-center rounded-full border border-line bg-white text-ink transition-colors hover:border-accent-500" @click="copy(pageUrl)">
              <Icon :name="copied ? 'lucide:check' : 'lucide:link'" class="size-4" />
              <span v-if="copied" role="status" class="absolute top-full right-0 mt-2 rounded-lg bg-ink px-2.5 py-1 text-xs whitespace-nowrap text-white">{{ t('page.copied') }}</span>
            </button>
          </div>
        </div>
      </header>

      <!-- Eski saytdagi joylashuv (canvas: "Yangilik maqolasi", "Maqola — tik surat"): chapda surat va matn, o'ngda so'nggi yangiliklar -->
      <div class="mx-auto grid max-w-7xl gap-12 px-4 pt-9 sm:px-6 lg:grid-cols-[minmax(0,1fr)_340px] lg:items-start lg:px-8">
        <div class="min-w-0">
          <!-- Asosiy surat: ustun kengligida, kesilmaydi. Hover — sekin kattalashadi; bosilsa to'liq ekranda ochiladi -->
          <button
            v-if="post.image"
            type="button"
            :aria-label="`${t('posts.zoom')}: ${post.title}`"
            class="group relative mx-auto block cursor-zoom-in overflow-hidden rounded-[28px] bg-brand-50 shadow-[0_30px_60px_-36px_rgba(19,17,47,0.55)]"
            :class="ratio === null ? 'w-fit max-w-full' : 'w-full'"
            :style="coverStyle"
            @click="viewerIndex = 0"
          >
            <img
              ref="coverImg"
              :src="post.image"
              :alt="post.title"
              fetchpriority="high"
              class="block transition-transform duration-700 ease-out group-hover:scale-[1.03] motion-reduce:transition-none motion-reduce:group-hover:scale-100"
              :class="ratio === null ? 'max-h-[1100px] w-auto max-w-full' : 'size-full object-cover'"
              @load="measure"
            >
            <span class="absolute right-4 bottom-4 inline-flex items-center gap-2 rounded-full bg-white/95 px-3.5 py-2 text-[13px] font-semibold text-ink opacity-0 shadow-[0_8px_24px_-10px_rgba(19,17,47,0.45)] transition duration-300 group-hover:opacity-100 group-focus-visible:opacity-100 pointer-coarse:opacity-100 max-sm:px-2.5">
              <Icon name="lucide:maximize-2" class="size-4" />
              <span class="max-sm:sr-only">{{ t('posts.zoom') }}</span>
            </span>
          </button>
          <div v-else class="decor relative aspect-[21/9] overflow-hidden rounded-[28px] bg-brand-800" aria-hidden="true">
            <span class="absolute -right-[8%] -bottom-[60%] aspect-square w-[45%] rounded-full border-[3.5rem] border-white/5" />
            <span class="absolute top-1/2 left-[6%] -translate-y-1/2 font-display text-[clamp(4rem,12vw,10rem)] leading-none text-accent-400/90 italic">“</span>
          </div>

          <!-- Tadbir: vaqt va joy -->
          <dl v-if="type === 'events' && (post.startsAt || post.location)" class="mt-10 grid gap-4 rounded-3xl bg-brand-50 p-6 sm:grid-cols-2">
            <div v-if="post.startsAt">
              <dt class="text-[13px] text-muted">{{ t('posts.when') }}</dt>
              <dd class="mt-1 font-semibold">{{ formatDate(post.startsAt) }}<template v-if="hasTime">, {{ formatDate(post.startsAt, 'time') }}</template></dd>
            </div>
            <div v-if="post.location">
              <dt class="text-[13px] text-muted">{{ t('posts.where') }}</dt>
              <dd class="mt-1 font-semibold">{{ post.location }}</dd>
            </div>
          </dl>

          <ProseHtml :html="post.body" lead class="mt-10" />
          <PostAttachments :items="post.attachments ?? []" />

          <div v-if="post.gallery.length" class="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-3">
            <button
              v-for="(src, i) in post.gallery"
              :key="src"
              type="button"
              :aria-label="`${t('posts.zoom')}: ${i + 1} / ${post.gallery.length}`"
              class="group relative aspect-[4/3] cursor-zoom-in overflow-hidden rounded-[18px] bg-brand-50"
              @click="viewerIndex = i + galleryOffset"
            >
              <img :src="src" alt="" loading="lazy" class="size-full object-cover transition-transform duration-500 ease-out group-hover:scale-105 motion-reduce:transition-none motion-reduce:group-hover:scale-100">
              <span class="absolute right-2.5 bottom-2.5 grid size-9 place-items-center rounded-full bg-white/95 text-ink opacity-0 shadow-sm transition-opacity duration-300 group-hover:opacity-100 group-focus-visible:opacity-100 pointer-coarse:opacity-100">
                <Icon name="lucide:maximize-2" class="size-4" />
              </span>
            </button>
          </div>

          <ul v-if="post.tags.length" class="mt-9 flex flex-wrap gap-2 border-t border-line pt-6 text-sm">
            <li v-for="tag in post.tags" :key="tag">
              <NuxtLink :to="{ path: localePath('/search'), query: { q: tag } }" class="inline-block rounded-full border border-line bg-white px-3.5 py-1.5 text-ink transition-colors hover:border-accent-500">#{{ tag }}</NuxtLink>
            </li>
          </ul>
        </div>

        <!-- So'nggi yangiliklar: kichik surat, sarlavha va sana; ekran aylanganda yonda yopishib turadi -->
        <aside v-if="post.latest.length" class="no-print min-w-0 rounded-3xl border border-line bg-white px-[22px] pt-[22px] pb-[18px] lg:sticky lg:top-36">
          <h2 class="text-lg font-semibold">{{ t('posts.latest') }}</h2>
          <ul class="mt-1.5">
            <li v-for="item in post.latest" :key="item.id" class="border-b border-line/70 py-3.5 last:border-0">
              <NuxtLink :to="localePath(`/${item.type}/${item.slug}`)" class="group flex items-start gap-3.5">
                <span class="relative h-[70px] w-[104px] shrink-0 overflow-hidden rounded-xl bg-brand-50">
                  <img v-if="item.image" :src="item.image" alt="" loading="lazy" class="size-full object-cover transition-transform duration-500 ease-out group-hover:scale-[1.06] motion-reduce:transition-none">
                  <span v-else class="grid size-full place-items-center"><BrandMark class="size-9 opacity-40" /></span>
                </span>
                <span class="min-w-0">
                  <span class="line-clamp-3 text-[15px] leading-snug font-semibold text-ink transition-colors group-hover:text-brand-700">{{ item.title }}</span>
                  <time :datetime="item.date" class="mt-1.5 flex items-center gap-1.5 text-[13px] font-medium text-accent-600">
                    <Icon name="lucide:calendar" class="size-3.5" />
                    {{ formatDate(item.date) }}
                  </time>
                </span>
              </NuxtLink>
            </li>
          </ul>
          <NuxtLink :to="localePath('/yangiliklar')" class="mt-2.5 flex h-11 items-center justify-center gap-1.5 rounded-[14px] bg-brand-50 text-sm font-semibold text-brand-800 transition-colors hover:bg-brand-100">
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

    <ImageViewer v-model:index="viewerIndex" :images="viewerImages" :caption="post.title" />
  </div>
</template>
