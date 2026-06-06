"""Descendant–ancestor alignment and correspondence-based scoring."""

import re


class Uralign:
    """Sequential alignment and scoring for etymological comparison.

    The API is language-pair agnostic: method names such as ``hu`` reflect
    historical use (Hungarian vs. proto-Uralic) but accept any two segment lists
    with CV profiles.

    Examples
    --------
    In a loanword-detection pipeline, align donor and recipient segments then
    score against mined correspondences::

        alm_d, alm_a = Uralign.hu(seg_d, seg_a, cv_d[0], cv_a[0])
        score = Uralign.get_score(alm_d, alm_a, scorer, freq_filter=2)

    Notes
    -----
    * **CLDF conversion** — ``Uralign.hu`` writes ``Uralign`` / ``Uralign_cluster``
      columns in cognate tables (UEW-hu, SeimaTurbino-hu).
    * **Quantitative analysis** — loanword-detection pipelines (e.g.
      Indo-Iranian–Hungarian ``make_results.py``) use ``Uralign.hu`` and
      ``Uralign.get_score`` with correspondence scorers from
      :func:`~loanpy.correspondences.get_sound_correspondences`.
    """

    @staticmethod
    def hu(
        seqHU: list[str],
        seqPU: list[str],
        seqHU_cv0: str,
        seqPU_cv0: str,
        initial_gap: bool = True,
        final_gap: bool = True,
    ) -> tuple[list[str], list[str]]:
        """Align two segment sequences with optional initial and final gap rules.

        Parameters
        ----------
        seqHU, seqPU:
            Segment lists (modified in place when gaps are inserted).
        seqHU_cv0, seqPU_cv0:
            Word-initial C/V labels for gap decisions.
        initial_gap:
            If True and the descendant begins with a vowel, prepend ``#-`` /
            ``-`` markers.
        final_gap:
            If True, pad or cluster the longer sequence at the word edge.

        Returns
        -------
        tuple[list[str], list[str]]
            Aligned segment pair.

        Notes
        -----
        Used in **CLDF conversion** and in **make_results.py** (loanword scoring).
        """
        if initial_gap:
            if seqHU_cv0 == "V":
                seqHU.insert(0, "#-")
                if seqPU_cv0 == "V":
                    seqPU.insert(0, "-")

        if final_gap:
            diff = abs(len(seqPU) - len(seqHU))
            if len(seqHU) < len(seqPU):
                seqHU.append("-#")
                seqPU = seqPU[:-diff] + [".".join(seqPU[-diff:])]
            elif len(seqHU) > len(seqPU):
                seqHU = seqHU[:-diff] + ["+"] + [".".join(seqHU[-diff:])]
        else:
            n = min(len(seqHU), len(seqPU))
            seqHU, seqPU = seqHU[:n], seqPU[:n]
        return seqHU, seqPU

    @staticmethod
    def get_score(
        seqA: list[str],
        seqB: list[str],
        scorer: dict[tuple[str, str], float],
        freq_filter: int = 2,
    ) -> int:
        """Sum correspondence scores along an alignment.

        For each aligned pair ``(a, b)`` the key ``(a, b)`` is looked up in
        ``scorer``. Pairs below ``freq_filter`` incur a large penalty.

        Parameters
        ----------
        seqA, seqB:
            Parallel aligned token lists.
        scorer:
            Mapping from correspondence keys to weights (often absolute
            frequencies from :func:`~loanpy.correspondences.get_sound_correspondences`).
        freq_filter:
            Minimum score for a pair to count positively.

        Returns
        -------
        int
            Aggregate alignment score.

        Notes
        -----
        Used in **make_results.py** together with scores from
        :func:`~loanpy.correspondences.get_sound_correspondences`.
        """
        score = 0
        for a, b in zip(seqA, seqB):
            local_score = scorer.get((a, b), -1000)
            if local_score >= freq_filter:
                score += local_score
            else:
                score -= 1000
        return score


class Altign:
    """Global-alignment helpers: gap collapsing and cluster-aware scoring.

    Used after LingPy global pairwise alignment when donor clusters may be
    longer than recipient tokens and partial cluster matches should count.

    Examples
    --------
    Typical workflow in loanword-detection pipelines::

        alm_hun, alm_donor = pw.alignments[0]
        alm_hun, alm_donor = Altign.gaps(alm_hun, alm_donor)
        score = Altign.get_score(alm_hun, alm_donor, scorer, freq_filter=2)

    Notes
    -----
    * **CLDF conversion** — ``Altign.gaps`` collapses consecutive gaps in
      WestOldTurkic ``Monogap`` alignments.
    * **Quantitative analysis** — Gothic–Hungarian and Turkic–Hungarian
      ``make_results.py`` use ``Altign.get_score`` with mined correspondences.
    """

    @staticmethod
    def gaps(seqA: list[str], seqB: list[str]) -> tuple[list[str], list[str]]:
        """Collapse consecutive gaps on ``seqB`` into a single gap per position.

        When two adjacent positions in ``seqB`` are gaps (``"-"``), the matching
        symbol in ``seqA`` is merged into the previous token. Trailing gaps may
        introduce a ``"+"`` marker in ``seqA``.

        Parameters
        ----------
        seqA, seqB:
            Parallel aligned token lists.

        Returns
        -------
        tuple[list[str], list[str]]
            Collapsed alignment pair.

        Notes
        -----
        Used in **CLDF conversion** for WestOldTurkic (``Monogap`` alignments) after
        global pairwise alignment.
        """
        seqA_new, seqB_new = [], []
        for idx, (tokA, tokB) in enumerate(zip(seqA, seqB)):
            if idx != 0 and tokB == "-" and seqB_new[-1] == "-":
                seqA_new[-1] += f".{tokA}"
            else:
                seqA_new.append(tokA)
                seqB_new.append(tokB)
        if seqB_new[-1] == "-":
            seqA_new.insert(-1, "+")
            seqB_new.pop(-1)
        return seqA_new, seqB_new

    @staticmethod
    def get_score(
        alm_hun: list[str],
        alm_donor: list[str],
        scorer: dict[tuple[str, str], float],
        freq_filter: int,
    ) -> int:
        """Score a global alignment with partial donor-cluster matching.

        For each aligned pair, look up ``(hu, donor)`` in ``scorer``. If the
        score is below ``freq_filter``, try shortening the donor cluster by
        dropping trailing dot-separated segments. Vowel-length mismatches
        (ignoring ``ː``) count as ``freq_filter`` when no correspondence matches.

        Parameters
        ----------
        alm_hun, alm_donor:
            Parallel aligned token lists.
        scorer:
            Mapping from correspondence keys to weights.
        freq_filter:
            Minimum score for a pair to count positively.

        Returns
        -------
        int
            Aggregate alignment score.

        Notes
        -----
        Used in **make_results.py** (Gothic–Hungarian, Turkic–Hungarian) with
        correspondences from :func:`~loanpy.correspondences.get_sound_correspondences`.
        """
        total = 0
        for a, b in zip(alm_hun, alm_donor):
            def best_local_score(hu, donor):
                local = scorer[(hu, donor)]
                if local >= freq_filter:
                    return local
                if "." in donor:
                    parts = donor.split(".")
                    while parts:
                        parts.pop()
                        cand = ".".join(parts)
                        local = scorer[(hu, cand)]
                        if local >= freq_filter:
                            return local
                return -1000

            local_score = best_local_score(a, b)
            if local_score >= freq_filter:
                total += local_score
            elif re.sub("ː", "", a) == re.sub("ː", "", b):
                total += freq_filter
            else:
                total -= 1000
        return total
