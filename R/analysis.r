# Read Data
glad <- read.csv("data/glad_mod44_bgr_areas.csv")
rap <- read.csv("data/rap_mod44_bgr_areas.csv")

# GLAD Bare Ground vs Modis Bare Ground @Village Level
with(glad, plot(glad_bgr_area, mod_bgr_area,
  main = "Village Bare Ground Area (2010)",
  xlab = "GLAD Bare Ground Area (ha)",
  ylab = "MOD44B Bare Ground Area (ha)"
))
abline(1, 1)
with(glad, cor(glad_bgr_area, mod_bgr_area))

# RAP Bareg Ground vs Modis Bare Ground - random sample
rap$mod_percent_dif <- (rap$mod_bgr_post - rap$mod_bgr_pre) /
  rap$mod_bgr_pre * 100

rap$rap_percent_dif <- (rap$rap_bgr_post - rap$rap_bgr_pre) /
  rap$rap_bgr_pre * 100
rap <- replace(rap, is.na(rap), 0)
rap$mod_dif <- rap$mod_bgr_post - rap$mod_bgr_pre
rap$rap_dif <- rap$rap_bgr_post - rap$rap_bgr_pre

with(rap, plot(rap_percent_dif, mod_percent_dif,
  main = "Bare Ground Change (%)",
  xlab = "RAP Change in Bare Ground (%)",
  ylab = "MOD44B Change in Bare Ground (%)",
))
abline(1, 1, col = "grey")
with(rap, cor(rap_dif, mod_dif))

rap$sign1 <- ifelse(rap$mod_di > 0, "Positive", "Negative")
rap$sign2 <- ifelse(rap$rap_di > 0, "Positive", "Negative")
different_signs <- subset(rap, sign1 != sign2)
table(rap$sign1, rap$sign2)
