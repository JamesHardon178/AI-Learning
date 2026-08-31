<template>
  <section v-if="citations?.length" class="citation-list">
    <div class="citation-list__title">来源</div>
    <div class="citation-list__items">
      <div v-for="(citation, index) in citations" :key="`${citation.source}-${index}`" class="citation-list__item">
        <el-tag size="small" effect="plain" class="citation-list__tag">引用 {{ index + 1 }}</el-tag>
        <div class="citation-list__meta">
          <div class="citation-list__source">📎 {{ citation.source }}</div>
          <div class="citation-list__chunk">Chunk {{ citation.chunk_index }}</div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  citations: {
    type: Array,
    default: () => []
  }
})
</script>
