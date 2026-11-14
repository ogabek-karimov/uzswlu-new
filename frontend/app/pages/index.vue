<script setup lang="ts">
const { data } = await useHomeData()
</script>

<template>
  <div>
    <HomeCarousel :slides="data?.slides ?? []" />
    <HomeBackdrop variant="glyphs">
      <HomeAbout class="pt-10 lg:pt-14" :stats="data?.stats ?? []" />
      <HomeQuickLinks class="pb-2" />
    </HomeBackdrop>
    <HomeFaculties class="mt-14 lg:mt-20" :faculties="data?.faculties ?? []" />
    <HomeBackdrop variant="newsprint">
      <HomeNews :news="data?.news ?? []" :announcements="data?.announcements ?? []" />
    </HomeBackdrop>
    <HomeEvents :events="data?.events ?? []" />
    <HomeContact />
    <HomeBanner :banner="data?.banner ?? null" />
    <HomeStateSymbols />
    <HomePartners :partners="data?.partners ?? []" />
  </div>
</template>
