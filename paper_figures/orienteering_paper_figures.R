options(stringsAsFactors = FALSE)

library(grid)

font_family <- "Microsoft YaHei"

draw_box <- function(x, y, w, h, label,
                     fill = "#F4F7FB",
                     col = "#3A506B",
                     lwd = 2,
                     fontsize = 14,
                     fontface = "plain") {
  grid.roundrect(
    x = unit(x, "npc"),
    y = unit(y, "npc"),
    width = unit(w, "npc"),
    height = unit(h, "npc"),
    r = unit(0.02, "snpc"),
    gp = gpar(fill = fill, col = col, lwd = lwd)
  )
  grid.text(
    label,
    x = unit(x, "npc"),
    y = unit(y, "npc"),
    gp = gpar(fontsize = fontsize, fontfamily = font_family, col = "#1F2933", fontface = fontface)
  )
}

draw_arrow <- function(x0, y0, x1, y1, col = "#5C677D", lwd = 2) {
  grid.lines(
    x = unit(c(x0, x1), "npc"),
    y = unit(c(y0, y1), "npc"),
    arrow = arrow(type = "closed", length = unit(0.18, "inches")),
    gp = gpar(col = col, lwd = lwd)
  )
}

draw_title <- function(title, subtitle = NULL) {
  grid.text(
    title,
    x = unit(0.5, "npc"),
    y = unit(0.95, "npc"),
    gp = gpar(fontsize = 20, fontfamily = font_family, fontface = "bold", col = "#0F172A")
  )
  if (!is.null(subtitle)) {
    grid.text(
      subtitle,
      x = unit(0.5, "npc"),
      y = unit(0.91, "npc"),
      gp = gpar(fontsize = 10, fontfamily = font_family, col = "#475569")
    )
  }
}

save_devices <- function(stem, drawer, width = 10, height = 6.5, res = 300) {
  png(filename = paste0(stem, ".png"), width = width, height = height, units = "in", res = res, bg = "white")
  grid.newpage()
  drawer()
  dev.off()

  pdf(file = paste0(stem, ".pdf"), width = width, height = height, family = font_family, bg = "white")
  grid.newpage()
  drawer()
  dev.off()

  svg(filename = paste0(stem, ".svg"), width = width, height = height, bg = "white")
  grid.newpage()
  drawer()
  dev.off()
}

figure1_draw <- function() {
  draw_title(
    "图1 体育核心素养与小学定向运动耦合机制图",
    "Theoretical coupling between core PE literacy and orienteering"
  )

  draw_box(0.16, 0.72, 0.18, 0.12, "运动能力", fill = "#DCEBFA", fontface = "bold")
  draw_box(0.16, 0.52, 0.18, 0.12, "健康行为", fill = "#DDF4E4", fontface = "bold")
  draw_box(0.16, 0.32, 0.18, 0.12, "体育品德", fill = "#FDE8D7", fontface = "bold")

  draw_box(0.50, 0.82, 0.20, 0.10, "地图识别", fill = "#EEF2FF")
  draw_box(0.50, 0.68, 0.20, 0.10, "路线规划", fill = "#EEF2FF")
  draw_box(0.50, 0.54, 0.20, 0.10, "奔跑耐力", fill = "#EEF2FF")
  draw_box(0.50, 0.40, 0.20, 0.10, "合作竞赛", fill = "#EEF2FF")
  draw_box(0.50, 0.26, 0.20, 0.10, "风险判断", fill = "#EEF2FF")

  draw_box(0.84, 0.72, 0.18, 0.10, "体能发展", fill = "#FFF3BF")
  draw_box(0.84, 0.58, 0.18, 0.10, "认知提升", fill = "#FFF3BF")
  draw_box(0.84, 0.44, 0.18, 0.10, "规则意识", fill = "#FFF3BF")
  draw_box(0.84, 0.30, 0.18, 0.10, "合作精神", fill = "#FFF3BF")

  draw_arrow(0.25, 0.72, 0.40, 0.82, col = "#5B8FF9")
  draw_arrow(0.25, 0.72, 0.40, 0.54, col = "#5B8FF9")
  draw_arrow(0.25, 0.52, 0.40, 0.68, col = "#52C41A")
  draw_arrow(0.25, 0.52, 0.40, 0.26, col = "#52C41A")
  draw_arrow(0.25, 0.32, 0.40, 0.40, col = "#FA8C16")
  draw_arrow(0.25, 0.32, 0.40, 0.26, col = "#FA8C16")

  draw_arrow(0.60, 0.82, 0.75, 0.58)
  draw_arrow(0.60, 0.68, 0.75, 0.58)
  draw_arrow(0.60, 0.54, 0.75, 0.72)
  draw_arrow(0.60, 0.40, 0.75, 0.30)
  draw_arrow(0.60, 0.26, 0.75, 0.44)

  grid.text(
    "定向运动活动要素",
    x = unit(0.50, "npc"),
    y = unit(0.14, "npc"),
    gp = gpar(fontsize = 14, fontfamily = font_family, col = "#334155", fontface = "bold")
  )
}

figure2_draw <- function() {
  draw_title(
    "图2 小学定向运动开展现状与问题归因图",
    "Current situation and four major problem clusters"
  )

  draw_box(0.50, 0.74, 0.28, 0.12, "小学定向运动开展现状", fill = "#DCEBFA", fontface = "bold", fontsize = 16)

  draw_box(0.22, 0.50, 0.28, 0.18,
           "课程开展不足\n- 目标模糊\n- 重理论轻实践\n- 递进性不足",
           fill = "#F8FAFC")
  draw_box(0.50, 0.50, 0.28, 0.18,
           "师资专业薄弱\n- 培训短期化\n- 技能掌握不系统\n- 方法创新不足",
           fill = "#F8FAFC")
  draw_box(0.78, 0.50, 0.28, 0.18,
           "场地器材受限\n- 校园地形单一\n- 校外组织困难\n- 器材老化不足",
           fill = "#F8FAFC")
  draw_box(0.50, 0.24, 0.34, 0.16,
           "评价体系单一\n- 偏重结果评价\n- 忽视过程反馈\n- 忽视健康行为与体育品德",
           fill = "#F8FAFC")

  draw_arrow(0.50, 0.68, 0.22, 0.59)
  draw_arrow(0.50, 0.68, 0.50, 0.59)
  draw_arrow(0.50, 0.68, 0.78, 0.59)
  draw_arrow(0.50, 0.68, 0.50, 0.32)

  grid.text(
    "说明：图中四类问题与论文“现状分析”和“问题分析”章节一一对应，可直接用于结构性归纳。",
    x = unit(0.5, "npc"),
    y = unit(0.08, "npc"),
    gp = gpar(fontsize = 10, fontfamily = font_family, col = "#475569")
  )
}

figure3_draw <- function() {
  draw_title(
    "图3 基于体育核心素养的小学定向运动发展策略闭环图",
    "Closed-loop strategy framework for implementation"
  )

  draw_box(0.50, 0.50, 0.24, 0.12, "体育核心素养提升", fill = "#FFF3BF", fontface = "bold", fontsize = 16)

  draw_box(0.50, 0.78, 0.24, 0.12, "优化课程设计", fill = "#DCEBFA", fontface = "bold")
  draw_box(0.78, 0.50, 0.24, 0.12, "加强师资培训", fill = "#DDF4E4", fontface = "bold")
  draw_box(0.50, 0.22, 0.28, 0.12, "整合场地器材资源", fill = "#FDE8D7", fontface = "bold")
  draw_box(0.22, 0.50, 0.26, 0.12, "完善多元评价体系", fill = "#FCE7F3", fontface = "bold")

  draw_arrow(0.50, 0.72, 0.68, 0.56, col = "#64748B")
  draw_arrow(0.72, 0.50, 0.56, 0.28, col = "#64748B")
  draw_arrow(0.50, 0.28, 0.30, 0.44, col = "#64748B")
  draw_arrow(0.28, 0.50, 0.44, 0.72, col = "#64748B")

  draw_arrow(0.50, 0.72, 0.50, 0.57, col = "#0EA5E9")
  draw_arrow(0.72, 0.50, 0.57, 0.50, col = "#16A34A")
  draw_arrow(0.50, 0.28, 0.50, 0.43, col = "#F97316")
  draw_arrow(0.28, 0.50, 0.43, 0.50, col = "#DB2777")

  draw_box(0.30, 0.08, 0.22, 0.08, "学生全面发展", fill = "#F8FAFC")
  draw_box(0.70, 0.08, 0.24, 0.08, "学校体育改革提质", fill = "#F8FAFC")
}

dir.create("paper_figures/output", recursive = TRUE, showWarnings = FALSE)

save_devices("paper_figures/output/figure1_coupling_mechanism", figure1_draw)
save_devices("paper_figures/output/figure2_problem_map", figure2_draw)
save_devices("paper_figures/output/figure3_strategy_loop", figure3_draw)
