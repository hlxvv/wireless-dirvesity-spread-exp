"""
Part 1: diversity combining experiment.

Students complete SC, MRC and a BER simulation over independent Rayleigh
flat fading branches.
"""

import numpy as np

from utils import (
    bpsk_demodulate,
    bpsk_modulate,
    calculate_ber,
    generate_bits,
    plot_ber_curve,
    plot_diversity_snapshot,
    rayleigh_fading_branches,
)
def _validate_branch_arrays(received, channel):
    received = np.asarray(received, dtype=complex)
    channel = np.asarray(channel, dtype=complex)
    if received.ndim != 2 or channel.ndim != 2:
        raise ValueError('received and channel must be 2-D arrays: branches x symbols')
    if received.shape != channel.shape:
        raise ValueError('received and channel must have the same shape')
    if received.shape[0] < 1 or received.shape[1] < 1:
        raise ValueError('received and channel must not be empty')
    if np.any(np.abs(channel) < 1e-12):
        raise ValueError('channel contains near-zero coefficients')
    return received, channel


def selection_combining(received, channel):
    """
    Selection combining for flat fading branches.

    Parameters:
        received: complex array with shape (num_branches, num_symbols).
        channel: complex channel coefficients with the same shape.

    Returns:
        combined: one-dimensional equalized symbol estimates.

    Requirement:
        For each symbol, select the branch with the largest |h|^2 and divide
        the selected received sample by its channel coefficient.
    """
    received, channel = _validate_branch_arrays(received, channel)

    # 1. 计算每个分支每个符号的信道功率 |h|²
    h_power = np.abs(channel) ** 2
    # 2. 对每个符号（每一列）找到功率最大的分支索引
    best_branch_idx = np.argmax(h_power, axis=0)
    # 3. 生成符号索引，用于花式索引取出对应分支的接收信号和信道
    symbol_indices = np.arange(received.shape[1])
    # 4. 取出每个符号对应最强分支的接收值和信道系数，做均衡
    selected_received = received[best_branch_idx, symbol_indices]
    selected_channel = channel[best_branch_idx, symbol_indices]
    combined = selected_received / selected_channel

    return combined


def maximal_ratio_combining(received, channel):
    """
    Maximal ratio combining for flat fading branches.

    Returns:
        combined = sum(conj(h_i) * r_i) / sum(|h_i|^2)
    """
    received, channel = _validate_branch_arrays(received, channel)

    # 1. 分子：每个分支的接收信号乘以信道共轭后按符号求和
    numerator = np.sum(np.conj(channel) * received, axis=0)
    # 2. 分母：每个符号所有分支的信道功率和
    total_power = np.sum(np.abs(channel) ** 2, axis=0)
    # 3. 归一化得到合并后的均衡符号
    combined = numerator / total_power

    return combined


def simulate_diversity_ber(snr_db_values, num_bits=4000, num_branches=2, seed=2026):
    """
    Simulate BER for no diversity, SC and MRC.

    Returns:
        dict with keys: '单分支', 'SC', 'MRC'. Each value is a list of BERs.
    """
    snr_db_values = np.asarray(snr_db_values, dtype=float)
    if snr_db_values.ndim != 1 or len(snr_db_values) == 0:
        raise ValueError('snr_db_values must be a non-empty one-dimensional array')
    if num_bits <= 0 or num_branches < 2:
        raise ValueError('num_bits must be positive and num_branches must be at least 2')

    # 1. 初始化各场景的BER存储列表
    ber_no_diversity = []  # 单分支无分集
    ber_sc = []            # 选择合并
    ber_mrc = []           # 最大比合并

    # 2. 生成固定的发送比特和调制符号，保证仿真可复现
    bits = generate_bits(num_bits, seed=seed)
    tx_symbols = bpsk_modulate(bits)

    # 3. 遍历每个SNR点仿真
    for snr_idx, snr_db in enumerate(snr_db_values):
        # 生成当前SNR下的多分支瑞利衰落接收信号和信道，seed随SNR变化保证独立同分布
        received, channel = rayleigh_fading_branches(
            tx_symbols, num_branches, snr_db, seed=seed + snr_idx
        )

        # --- 单分支无分集场景：取第一个分支直接均衡 ---
        eq_no_div = received[0] / channel[0]
        bits_hat_no_div = bpsk_demodulate(eq_no_div)
        ber_no_diversity.append(calculate_ber(bits, bits_hat_no_div))

        # --- 选择合并SC场景 ---
        eq_sc = selection_combining(received, channel)
        bits_hat_sc = bpsk_demodulate(eq_sc)
        ber_sc.append(calculate_ber(bits, bits_hat_sc))

        # --- 最大比合并MRC场景 ---
        eq_mrc = maximal_ratio_combining(received, channel)
        bits_hat_mrc = bpsk_demodulate(eq_mrc)
        ber_mrc.append(calculate_ber(bits, bits_hat_mrc))

    # 4. 返回要求格式的BER字典
    return {
        '单分支': ber_no_diversity,
        'SC': ber_sc,
        'MRC': ber_mrc
    }


def equal_gain_combining(received, channel):
    """Optional: equal-gain combining with phase-only correction."""
    received, channel = _validate_branch_arrays(received, channel)

    # 等增益合并逻辑：仅补偿信道相位，各分支等权重相加
    # 1. 计算相位校正权重：信道共轭 / 信道幅度，仅保留相位补偿
    phase_weights = np.conj(channel) / np.abs(channel)
    # 2. 各分支相位校正后求和
    combined_signal = np.sum(phase_weights * received, axis=0)
    # 3. 除以各分支幅度和做均衡，得到符号估计（如果只看BER也可以省略这步，不影响符号正负判断）
    total_amplitudes = np.sum(np.abs(channel), axis=0)
    combined = combined_signal / total_amplitudes

    return combined

# ------------------------------
# 选做扩展：如果要对比EGC性能，可以修改simulate_diversity_ber函数，新增EGC的BER统计
# 示例修改（可选）：
# def simulate_diversity_ber(snr_db_values, num_bits=4000, num_branches=2, seed=2026):
#     # ... 原有逻辑不变 ...
#     ber_egc = []
#     for ...:
#         # ... 原有逻辑不变 ...
#         eq_egc = equal_gain_combining(received, channel)
#         bits_hat_egc = bpsk_demodulate(eq_egc)
#         ber_egc.append(calculate_ber(bits, bits_hat_egc))
#     return {
#         '单分支': ber_no_diversity,
#         'SC': ber_sc,
#         'MRC': ber_mrc,
#         'EGC': ber_egc  # 新增EGC曲线
#     }
# ------------------------------


def run_diversity_demo():
    """Run Part 1 demo and generate figures."""
    print('=' * 60)
    print('Part 1: 分集合并实验')
    print('=' * 60)
    snr_db_values = np.array([0, 3, 6, 9, 12, 15], dtype=float)

    try:
        ber_curves = simulate_diversity_ber(snr_db_values, num_bits=6000, num_branches=2, seed=2026)
        plot_ber_curve(snr_db_values, ber_curves, '瑞利衰落信道下分集合并 BER 对比', 'diversity_ber_curve.png')

        bits = generate_bits(120, seed=7)
        symbols = bpsk_modulate(bits)
        received, channel = rayleigh_fading_branches(symbols, 2, snr_db=8, seed=17)
        branch_equalized = received[0] / channel[0]
        mrc_output = maximal_ratio_combining(received, channel)
        plot_diversity_snapshot(symbols, branch_equalized, mrc_output, 'diversity_waveform_snapshot.png')

        print('[OK] 已生成 results/diversity_ber_curve.png')
        print('[OK] 已生成 results/diversity_waveform_snapshot.png')
    except NotImplementedError as error:
        print(f'[WAIT] 尚未完成核心函数: {error}')
    except Exception as error:
        print(f'[FAIL] Part 1 运行失败: {error}')


if __name__ == '__main__':
    run_diversity_demo()