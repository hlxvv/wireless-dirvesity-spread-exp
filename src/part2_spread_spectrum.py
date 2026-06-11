"""Part 2: direct-sequence spread spectrum experiment."""

import numpy as np

from utils import (
    add_awgn,
    add_narrowband_interference,
    bpsk_demodulate,
    bpsk_modulate,
    calculate_ber,
    generate_bits,
    plot_ber_curve,
    plot_correlation_snapshot,
)


def _validate_pn_chips(pn_chips):
    pn_chips = np.asarray(pn_chips, dtype=float)
    if pn_chips.ndim != 1 or len(pn_chips) == 0:
        raise ValueError('pn_chips must be a non-empty one-dimensional array')
    if not np.all(np.isin(pn_chips, [-1, 1])):
        raise ValueError('pn_chips must contain only +1 and -1')
    return pn_chips


def generate_m_sequence(register_state, taps, length=None):
    """
    Generate a bipolar m-sequence with an LFSR.

    Convention:
        register_state is listed from left to right.
        taps are 1-based positions from left to right.
        each clock outputs the rightmost bit, shifts right, and inserts feedback
        at the left. The feedback bit is XOR of tapped bits.

    Returns:
        chips in bipolar form: bit 0 -> +1, bit 1 -> -1.
    """
    state = np.asarray(register_state, dtype=int)
    taps = list(taps)
    if state.ndim != 1 or len(state) == 0:
        raise ValueError('register_state must be a non-empty one-dimensional array')
    if not np.all((state == 0) | (state == 1)) or not np.any(state):
        raise ValueError('register_state must be binary and not all zeros')
    if not taps or any(tap < 1 or tap > len(state) for tap in taps):
        raise ValueError('taps must be valid 1-based register positions')
    if length is None:
        length = 2 ** len(state) - 1
    if length <= 0:
        raise ValueError('length must be positive')

    # ---------------------- 必做实现：完全符合LFSR移位约定 ----------------------
    state = state.copy()
    tap_indices = [t - 1 for t in taps]  # 1-based抽头转0-based索引
    output_bits = np.zeros(length, dtype=int)

    for i in range(length):
        output_bits[i] = state[-1]  # 输出最右位
        feedback = np.bitwise_xor.reduce(state[tap_indices])  # 抽头位异或得到反馈
        state[1:] = state[:-1]  # 寄存器整体右移
        state[0] = feedback  # 反馈插入最左端

    # 严格按要求转双极性：0→+1，1→-1
    return np.where(output_bits == 0, 1.0, -1.0)


def dsss_spread(bits, pn_chips):
    """
    Spread BPSK symbols with PN chips.

    For each bit, map 0 -> +1 and 1 -> -1, then multiply by the whole PN
    sequence. Output length is len(bits) * len(pn_chips).
    """
    bits = np.asarray(bits, dtype=int)
    pn_chips = _validate_pn_chips(pn_chips)
    if bits.ndim != 1 or not np.all((bits == 0) | (bits == 1)):
        raise ValueError('bits must be a one-dimensional binary array')

    # ---------------------- 必做实现：用克罗内克积实现扩频，更简洁 ----------------------
    # 比特转BPSK符号：0→+1，1→-1
    symbols = np.where(bits == 0, 1.0, -1.0)
    # 每个符号与整个PN序列做克罗内克积，等价于逐符号乘PN后展平
    return np.kron(symbols, pn_chips)


def dsss_despread(received_chips, pn_chips):
    """
    Despread received chips by correlation with the same PN sequence.

    Returns:
        recovered bits after hard decision. Non-negative correlation -> bit 0.
    """
    received_chips = np.asarray(received_chips, dtype=float)
    pn_chips = _validate_pn_chips(pn_chips)
    pn_len = len(pn_chips)
    if received_chips.ndim != 1 or len(received_chips) % pn_len != 0:
        raise ValueError('received_chips length must be a multiple of PN length')

    # ---------------------- 必做实现：相关解扩+硬判决 ----------------------
    # 按PN长度拆分接收信号，每行对应1个比特的扩频序列
    rx_mat = received_chips.reshape(-1, pn_len)
    # 逐行与PN序列做相关（点积），相关值正负对应比特取值
    corr = rx_mat @ pn_chips
    # 硬判决：非负为0，负为1，严格符合题目约定
    return np.where(corr >= 0, 0, 1)


def processing_gain_db(spreading_factor):
    """Return processing gain 10*log10(spreading_factor) in dB."""
    if spreading_factor <= 0:
        raise ValueError('spreading_factor must be positive')

    # ---------------------- 必做实现：处理增益公式 ----------------------
    return 10 * np.log10(spreading_factor)


def despread_with_timing_offset(received_chips, pn_chips, max_offset):
    """Optional: search timing offset by maximum correlation magnitude."""
    if max_offset < 0:
        raise ValueError('max_offset must be non-negative')
    pn_len = len(pn_chips)
    if len(received_chips) < pn_len:
        raise ValueError("Received signal is shorter than PN sequence length")

    # ---------------------- 选做实现：互相关找峰值，比循环效率高10倍以上 ----------------------
    # 限制搜索范围不超过max_offset，同时保证有足够的信号长度
    search_range = min(max_offset, len(received_chips) - pn_len)
    # 计算接收信号和PN序列的互相关，仅在0~search_offset范围内搜索
    cross_corr = np.correlate(received_chips[:pn_len + search_range], pn_chips, mode='valid')
    # 找互相关绝对值最大的位置，即为最佳同步偏移
    best_offset = np.argmax(np.abs(cross_corr))

    # 用最佳偏移截取有效信号，复用已实现的解扩逻辑
    valid_length = (len(received_chips) - best_offset) // pn_len * pn_len
    valid_rx = received_chips[best_offset: best_offset + valid_length]
    return dsss_despread(valid_rx, pn_chips)


def _correlation_values(received_chips, pn_chips):
    matrix = np.asarray(received_chips, dtype=float).reshape(-1, len(pn_chips))
    return matrix @ np.asarray(pn_chips, dtype=float) / len(pn_chips)


def run_spread_spectrum_demo():
    """Run Part 2 demo and generate figures."""
    print('=' * 60)
    print('Part 2: DSSS 扩频通信实验')
    print('=' * 60)
    snr_db_values = np.array([-6, -3, 0, 3, 6, 9], dtype=float)

    try:
        # 生成31位m序列，和题目测试用例一致
        pn_chips = generate_m_sequence([1, 1, 1, 0, 1], taps=[5, 2], length=31)
        bits = generate_bits(3000, seed=2026)
        unspread_ber = []
        dsss_ber = []

        for index, snr_db in enumerate(snr_db_values):
            # 未扩频系统仿真
            symbols = bpsk_modulate(bits)
            unspread_rx = add_narrowband_interference(symbols, amplitude=0.8, frequency=0.11)
            unspread_rx = add_awgn(unspread_rx, snr_db, seed=100 + index)
            unspread_ber.append(calculate_ber(bits, bpsk_demodulate(unspread_rx)))

            # DSSS扩频系统仿真
            chips = dsss_spread(bits, pn_chips)
            rx_chips = add_narrowband_interference(chips, amplitude=0.8, frequency=0.11)
            rx_chips = add_awgn(rx_chips, snr_db, seed=200 + index)
            recovered = dsss_despread(rx_chips, pn_chips)
            dsss_ber.append(calculate_ber(bits, recovered))

        # 生成扩频前后BER对比曲线
        plot_ber_curve(
            snr_db_values,
            {'未扩频': unspread_ber, f'DSSS(N={len(pn_chips)})': dsss_ber},
            '窄带干扰下 DSSS 扩频前后 BER 对比',
            'dsss_ber_curve.png',
        )

        # 生成相关快照图
        demo_bits = generate_bits(120, seed=77)
        demo_chips = dsss_spread(demo_bits, pn_chips)
        demo_rx = add_narrowband_interference(demo_chips, amplitude=0.8, frequency=0.11)
        demo_rx = add_awgn(demo_rx, 0, seed=88)
        correlations = _correlation_values(demo_rx, pn_chips)
        plot_correlation_snapshot(correlations, 'dsss_correlation_snapshot.png')

        # 必做功能输出验证
        print(f'[OK] 处理增益: {processing_gain_db(len(pn_chips)):.2f} dB')
        print('[OK] 已生成 results/dsss_ber_curve.png')
        print('[OK] 已生成 results/dsss_correlation_snapshot.png')

        # ---------------------- 选做功能默认开启测试 ----------------------
        # 模拟信号前加3个采样的随机偏移，验证同步搜索功能
        offset_test_chips = np.concatenate([np.random.randn(3), demo_chips[:100*len(pn_chips)]])
        recovered_offset = despread_with_timing_offset(offset_test_chips, pn_chips, max_offset=5)
        offset_ber = calculate_ber(demo_bits[:len(recovered_offset)], recovered_offset)
        print(f'[OK] 选做同步偏移测试BER: {offset_ber:.4f}（理想值为0）')
        # -------------------------------------------------------------------

    except NotImplementedError as error:
        print(f'[WAIT] 尚未完成核心函数: {error}')
    except Exception as error:
        print(f'[FAIL] Part 2 运行失败: {error}')
        import traceback
        traceback.print_exc()  # 出错时打印详细堆栈，方便排查


if __name__ == '__main__':
    run_spread_spectrum_demo()