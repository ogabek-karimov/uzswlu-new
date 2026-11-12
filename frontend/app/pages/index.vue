<script setup lang="ts">
const { data } = await useHomeData()

const students = computed(() => data.value?.stats.find(s => s.key === 'students'))
</script>

<template>
  <div>
    <HomeCarousel :slides="data?.slides ?? []" />
    <HomeHero :students="students" :news="data?.news ?? []" />
    <HomeToday :events="data?.events ?? []" />
    <div class="mt-12 lg:mt-16">
      <HomeGreetings />
    </div>
    <HomeAbout :stats="data?.stats ?? []" :updated-at="data?.updatedAt" />
    <HomeQuickLinks />
    <HomeLanguages :languages="data?.languages ?? []" />
    <HomeAdmission />
    <HomeFaculties :faculties="data?.faculties ?? []" />
    <HomeNews :news="data?.news ?? []" :announcements="data?.announcements ?? []" />
    <HomeEvents :events="data?.events ?? []" />
    <HomeStateSymbols />
    <HomePartners :partners="data?.partners ?? []" />
  </div>
</template>
