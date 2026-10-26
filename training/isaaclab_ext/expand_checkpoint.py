"""Widen an RSL-RL checkpoint's actor and critic inputs, so a blind walker can start training with new sensors.

The new inputs are appended at the end of each observation vector (that is where ``course_depth_cfg.py`` adds the
ToF term). Their first-layer weights are zero, so the widened network computes exactly the same actions and values as
the original until training changes them. The input normalizers get mean 0 / variance 1 for the new inputs (the ToF
term is already scaled), and the Adam optimizer state is padded with zeros the same way.

    python expand_checkpoint.py IN.pt OUT.pt --actor-add 64 --critic-add 64
"""

import argparse

import torch


def _pad_cols(t: torch.Tensor, n: int, value: float = 0.0) -> torch.Tensor:
    return torch.cat([t, torch.full((*t.shape[:-1], n), value, dtype=t.dtype, device=t.device)], dim=-1)


def widen(state: dict, add: int) -> tuple[dict, tuple[int, int]]:
    state = dict(state)
    old = tuple(state["mlp.0.weight"].shape)
    state["mlp.0.weight"] = _pad_cols(state["mlp.0.weight"], add)
    state["obs_normalizer._mean"] = _pad_cols(state["obs_normalizer._mean"], add, 0.0)
    state["obs_normalizer._var"] = _pad_cols(state["obs_normalizer._var"], add, 1.0)
    state["obs_normalizer._std"] = _pad_cols(state["obs_normalizer._std"], add, 1.0)
    return state, old


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--actor-add", type=int, required=True)
    ap.add_argument("--critic-add", type=int, required=True)
    a = ap.parse_args()
    ck = torch.load(a.src, map_location="cpu", weights_only=False)
    ck["actor_state_dict"], actor_old = widen(ck["actor_state_dict"], a.actor_add)
    ck["critic_state_dict"], critic_old = widen(ck["critic_state_dict"], a.critic_add)
    padded = 0
    for st in ck["optimizer_state_dict"]["state"].values():
        for key in ("exp_avg", "exp_avg_sq"):
            t = st.get(key)
            if t is not None and tuple(t.shape) == actor_old:
                st[key] = _pad_cols(t, a.actor_add)
                padded += 1
            elif t is not None and tuple(t.shape) == critic_old:
                st[key] = _pad_cols(t, a.critic_add)
                padded += 1
    torch.save(ck, a.dst)
    print(f"actor first layer {actor_old} -> {tuple(ck['actor_state_dict']['mlp.0.weight'].shape)}, "
          f"critic {critic_old} -> {tuple(ck['critic_state_dict']['mlp.0.weight'].shape)}, "
          f"optimizer tensors padded: {padded}, iteration {ck['iter']} -> {a.dst}")


if __name__ == "__main__":
    main()
