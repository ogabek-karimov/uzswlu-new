// robots.txt: mantiq — shared/utils/seo.ts (buildRobotsTxt)
export default defineEventHandler((event) => {
  setResponseHeader(event, 'content-type', 'text/plain; charset=utf-8')
  setResponseHeader(event, 'cache-control', 'public, max-age=3600')
  return buildRobotsTxt(siteOrigin(event), LOCALES)
})
