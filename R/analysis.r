glad <- read.csv("data/glad_mod44_bgr_areas.csv")
rap <- read.csv("data/rap_mod44_bgr_areas.csv")
ag <- read.csv("data/village_ag_areas.csv")

head(glad)
with(glad, plot(glad_bgr_area, mod_bgr_area,
  main = "Village Bare Ground Area (2010)",
  xlab = "GLAD Area (ha)",
  ylab = "MOD44B Area (ha)",
))
with(glad, cor(glad_bgr_area, mod_bgr_area))


abline(1, 1)

head(rap)
with(rap, plot(mod_bgr_post, rap_bgr_post))
with(rap, plot(mod_bgr_pre, rap_bgr_pre))

rap$mod_percent_dif <- (rap$mod_bgr_post - rap$mod_bgr_pre) /
  rap$mod_bgr_pre * 100

rap$rap_percent_dif <- (rap$rap_bgr_post - rap$rap_bgr_pre) /
  rap$rap_bgr_pre * 100

rap$mod_dif <- rap$mod_bgr_post - rap$mod_bgr_pre

rap$rap_dif <- rap$rap_bgr_post - rap$rap_bgr_pre

with(rap, plot(mod_dif, rap_dif))
with(rap, cor(mod_dif, rap_dif))
abline(1, 1)
rap$sign1 <- ifelse(rap$mod_di > 0, "Positive", "Negative")
rap$sign2 <- ifelse(rap$rap_di > 0, "Positive", "Negative")
different_signs <- subset(rap, sign1 != sign2)
head(different_signs)
mean(different_signs$mod_dif)
mean(different_signs$rap_dif)
table(rap$sign1, rap$sign2)

data$MOD_DIF <- (data$MOD_BGR_POST - data$MOD_BGR_PRE) /
  data$MOD_BGR_PRE * 100

data$RAP_DIF <- (data$RAP_BGR_POST - data$RAP_BGR_PRE) /
  data$RAP_BGR_PRE * 100

data <- na.omit(data)
with(data, plot(RAP_DIF, MOD_DIF))
abline(1, 1)
with(data, cor.test(RAP_DIF, MOD_DIF))

with(data, range(RAP_DIF))

lm <- with(data, lm(RAP_DIF ~ MOD_DIF))
summary(lm)
