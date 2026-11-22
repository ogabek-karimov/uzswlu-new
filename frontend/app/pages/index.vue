<script setup lang="ts">
const { data } = await useHomeData()
</script>

<template>
  <div>
    <HomeCarousel :slides="data?.slides ?? []" />
    <HomeBackdrop variant="paper">
      <HomeAbout v-reveal class="pt-10 lg:pt-14" :stats="data?.stats ?? []" :video-tour="data?.videoTour ?? null" />
      <HomeQuickLinks v-reveal class="pb-10" />
    </HomeBackdrop>
    <HomeFaculties v-reveal :faculties="data?.faculties ?? []" />
    <HomeBackdrop v-reveal variant="white" class="section-wave pb-12 lg:pb-16">
      <HomeNews show="news" :news="data?.news ?? []" :announcements="data?.announcements ?? []" />
    </HomeBackdrop>
    <HomeBackdrop v-if="data?.announcements?.length" v-reveal variant="paper">
      <HomeNews show="announcements" :news="data?.news ?? []" :announcements="data?.announcements ?? []" />
    </HomeBackdrop>
    <HomeEvents v-reveal :events="data?.events ?? []" />
    <HomeContact v-reveal :faculties="data?.faculties ?? []" />
    <HomeBanner v-reveal :banner="data?.banner ?? null" />
    <HomeStateSymbols v-reveal />
    <HomePartners v-reveal :partners="data?.partners ?? []" />
  </div>
</template>
