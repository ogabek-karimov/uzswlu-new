<script setup lang="ts">
const { data } = await useHomeData()
</script>

<template>
  <div>
    <HomeCarousel :slides="data?.slides ?? []" />
    <HomeAbout class="mt-10 lg:mt-14" :stats="data?.stats ?? []" />
    <HomeQuickLinks />
    <HomeFaculties class="mt-14 lg:mt-20" :faculties="data?.faculties ?? []" />
    <HomeNews :news="data?.news ?? []" :announcements="data?.announcements ?? []" />
    <HomeEvents :events="data?.events ?? []" />
    <HomeContact />
    <HomeBanner :banner="data?.banner ?? null" />
    <HomeStateSymbols />
    <HomePartners :partners="data?.partners ?? []" />
  </div>
</template>
