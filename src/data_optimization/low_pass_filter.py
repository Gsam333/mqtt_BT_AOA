# 低通滤波函数
def low_pass_filter(x, y, alfa=0.2):
    """低通滤波计算"""
    global preX, preY
    if 'preX' not in globals():
        preX = x
    if 'preY' not in globals():
        preY = y
    
    FX = x * alfa + preX * (1 - alfa)
    FY = y * alfa + preY * (1 - alfa)
    
    preX, preY = FX, FY  # 更新历史值
    return FX, FY

if __name__ == "__main__":
    pass