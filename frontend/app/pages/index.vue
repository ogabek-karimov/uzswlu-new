<script setup lang="ts">
const { data } = await useHomeData()

const students = computed(() => data.value?.stats.find(s => s.key === 'students'))
</script>

<template>
  <div>
    <HomeCarousel :slides="data?.slides ?? []" />
    <HomeHero :students="students" />
    <HomeQuickLinks />
    <HomeAbout :stats="data?.stats ?? []" :updated-at="data?.updatedAt" />
    <HomeFaculties :faculties="data?.faculties ?? []" />
    <HomeNews :news="data?.news ?? []" :announcements="data?.announcements ?? []" />
    <HomeEvents :events="data?.events ?? []" />
    <HomeLanguages :languages="data?.languages ?? []" />
    <HomeAdmission />
    <HomeStateSymbols />
    <HomePartners :partners="data?.partners ?? []" />
  </div>
</template>
