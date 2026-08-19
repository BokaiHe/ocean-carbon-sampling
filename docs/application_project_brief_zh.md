# Ocean Carbon Sampling：PhD 申请作品集项目简介

本项目构建了一个可复现的海洋碳观测系统模拟框架，用于比较固定观测数量下不同采样几何对未观测海域月度 pCO₂ 重建的影响。在默认口径下（whole-block 验证、球面面积加权、候选池与评价域同时限制在 60°N 以南），复制历史观测格局使 MAE 相对 random 增加 15.67%，在 15/15 个 year–fold 单元中一致更差。一个初始看似显著的全球 signed bias 在面积加权和可行域对齐后由 −4.954 收缩至 −0.473 µatm，因此被重新定性为 estimand 敏感性案例，而不是项目的核心科学发现。

## 问题与方法

“样本越多通常越准确”不能回答有限海洋碳观测应当放在哪里。因此，本项目固定 sample count、重建模型和评价数据，仅改变观测位置的分配方式，比较 random、历史观测密度和季节配平的空间覆盖策略。研究先以 SOCAT v2025 完成南大洋最小实验，再以 CMIP6 IPSL-CM6A-LR historical `r1i1p1f1` 建立全球 observing-system simulation experiment（OSSE）：月度 `spco2` 作为完整 truth，`tos` 和 `sos` 作为预测变量，SOCAT 仅定义 1990–2004 年历史观测权重，从而避免用观测重建产品作为 truth 的循环论证。

严格验证使用 2005、2010 和 2014 三个预设年份、五个 20° × 10° spatial-block folds 和 20 个配对 sampling seeds；同一位置的 12 个月始终进入同一 fold。所有策略共享固定的梯度提升模型。默认结果使用 sample count 5,000、whole-block validation、球面 1° cell-area weighting，并将候选池与评价域共同限制在 60°N 以南。

## 结果与解释

默认 random 基线的 MAE 为 11.836 µatm、RMSE 为 25.422 µatm。历史观测格局的 MAE 为 13.691 µatm，增加 1.855 µatm（15.67%），且在全部 15 个 year–fold 中更差；RMSE 增加 1.310 µatm（5.15%），在 12/15 个单元中更差。其 signed-bias difference 为 −0.473 µatm，因此核心结论是稳定的误差幅度惩罚，而不是稳定的全球系统偏移。

Coverage 是有边界的次要结果：默认 MAE 几乎不变，而 RMSE 较低；分位数审计表明该组合受罕见大误差影响，不能解释为整体精度普遍提高。在原始全域、等格点的支持性诊断中，历史策略的惩罚集中于结构性零覆盖区，而非沿正采样密度连续变化；该分解尚未在默认口径下重做，因此不被当作默认结果的因果解释。

## 方法学价值与边界

项目通过配对 seeds、预设年份与空间 folds、月份平衡审计、绝对基线、多误差尺度以及 regridding、面积权重和评价域审计控制替代解释。XGBoost/SHAP 因未通过 spatially grouped out-of-fold 泛化门槛而未被包装成机制解释。15 个 year–fold 仅是描述性一致性单元，不构成正式显著性检验。结论仍限于单一 Earth system model、ensemble member 和主重建模型；60°N 限制是可行域代理而非海冰掩膜，也尚未量化 pCO₂ 误差对应的全球碳通量影响。
