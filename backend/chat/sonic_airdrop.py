def get_points_and_gems_details():
    return f"""
{get_points_details()}

{get_gems_details()}
"""


def get_points_details():
    return f"""
Sonic Points are user-focused airdrop points that can be earned as part of the ~200 million S airdrop. Designed to boost liquidity on Sonic and strengthen its ecosystem, our points program positions Sonic as a premier hub for DeFi enthusiasts and users seeking to maximize the potential of their assets.

To earn Sonic Points, hold and use whitelisted assets across various DeFi apps. These points will be distributed over multiple seasons as NFT positions, ensuring long-term sustainability and preventing sudden supply shifts. The first season began with Sonic's launch and will conclude in June 2025.

— How To Earn Points
    — Passive Points
    — Activity Points
    — App Points (Gems)
— Whitelisted Assets
— Airdrop Points Dashboard
— Sonic Arcade Points
— Terms and Conditions

How To Earn Points
1. Passive Points — Hold Assets
Users can earn passive points by holding whitelisted assets directly in their Web3 wallets, such as Rabby or MetaMask, including hardware wallets. Assets held on centralized exchanges are not eligible.

Please note that WETH, scUSD, scETH, scBTC, LBTC, SolvBTC, and SolvBTC.BBN earn activity points only, not passive points.


2. Activity Points — Deploy Assets on Apps
By deploying whitelisted assets as liquidity on participating apps, users will earn activity points, which provide 2x the amount of points compared to simply holding assets passively. A list of participating apps is available on the points dashboard.


3. App Points (Gems) — Earn Further Allocation
The S airdrop includes a developer-focused portion, where apps compete for an airdrop allocation known as Sonic Gems. Apps can redeem these Gems for S tokens, which they can then distribute to their users however they want.

To decide how these S tokens are distributed to their users, each app will run its own independent points program, entirely at its discretion. The app may consider various things, such as the amount of liquidity a user has deployed, the duration of deployment, and the specific pools to which a user has added liquidity.

As a user, you will be earning passive and activity points regardless. Your goal is to identify which app has the points program that will offer the highest return for your liquidity. The challenge lies in maximizing your overall rewards by combining the yield earned from providing liquidity with the points earned from the app's points program.


Whitelisted Assets
To qualify for the S airdrop, you must hold or use the whitelisted assets listed in the table below. The multipliers are applied to the passive or activity points you earn.

Asset                                                                          Multiplier
scUSD, stkscUSD, wstkscUSD                                                     6x (Boosted)
USDC.e                                                                         5x (Boosted)
s, wS, stS, OS, scETH, stkscETH, wstkscETH, scBTC, stkscBTC, wstkscBTC         4x (Boosted)
WETH, LBTC, SolvBTC, SolvBTC.BBN, x33                                          2x (Boosted)

Please note that WETH, scUSD, scETH, scBTC, LBTC, SolvBTC, and SolvBTC.BBN earn activity points only, not passive points.

Some whitelisted assets are boosted in the first 3 months after Sonic’s launch to encourage their usage and attract more liquidity to Sonic. After this period, we may choose to extend or reduce boosts.

Whitelisted assets and their multipliers are subject to change. S tokens staked through MySonic are not eligible for points. Users who wish to stake can instead use stS by Beets, a liquid staking token.

Learn more about scUSD/scETH by Rings. Sonic Labs makes no guarantee to the safety or peg of third-party assets, such as Rings. Use them at your own risk.

Airdrop Points Dashboard
The Sonic points dashboard is a comprehensive platform where users can:

Check earned points

Check the list of participating apps

Get whitelisted assets through a simple interface

Generate a referral code and share with friends to earn extra points

View a leaderboard that displays the points and Gems earned by users and apps

Sonic Arcade Points
The Sonic Arcade was a digital playground on the Sonic testnet that featured three play-to-earn games — Plinko, Mines, and Wheel — each offering airdrop points.

Arcade players will receive their points at the end of the S airdrop's first season.
"""


def get_gems_details():
    return f"""
Sonic Gems are developer-focused airdrop points designed to reward apps for driving user engagement and innovation. These Gems can be redeemed for S tokens, which apps can then distribute as rewards to their users.

This system helps apps grow by driving consistent user activity and maintaining long-term engagement. Gems are distributed across multiple seasons, ensuring a dynamic and sustainable reward structure. The first season is set to end around June 2025.

— What are Sonic Gems?
— Gems Season 1
— Distribution of Gems
— Gems Revocation Policy
— Example Distribution of Gems

What are Sonic Gems?
Sonic Gems are airdrop points exclusively designed for apps. Each season, a fixed supply of Gems is allocated to apps based on performance metrics. Apps can track their progress through the points dashboard.

To distribute the S tokens earned through Gems to their users, apps must manage the process independently. For example, an app could:

Mint a new token representing its share of Gems.

Maintain an internal record of user balances.

Use the third-party Merkl program

Join Sonic Builders on Telegram for further support

Unlike Sonic Points, which are airdrop points designed for users, Gems empower apps to claim liquid S tokens instead of vested NFT airdrop position. Once the S tokens are claimed, it’s the app’s responsibility to determine how they’re distributed to their users.

While there’s no strict requirement for apps to share a specific percentage of their claimed S tokens with their users, the design of Gems incentivizes generosity. Apps that share a larger portion of their claimed S with their communities are rewarded more favorably compared to those that do not.

Gems Season 1
A total of 1,680,000 Gems will be distributed during season 1. Out of this, 262,500 Gems are pre-allocated to Sonic Boom winners. The chart below shows the number of Gems allocated to each tier in Sonic Boom.

Category            Gems Per Winner
Emerald             13,125
Sapphire            8,750
Ruby                4,375

The remaining 1,417,500 Gems will be available for any app to earn throughout the season — whether they’re Sonic Boom winners or not. At the end of season 1, all eligible apps will be able to claim S tokens based on the number of Gems they have earned.

Distribution of Gems
Sonic Gems are distributed by considering factors such as category type, Sonic exclusivity, and effective reward distribution, promoting fairness and incentivizing active participation. 

The competitive PvP nature and fixed supply of Gems mean that an app's Gem balance may fluctuate daily, influenced by the performance of other apps on the platform.

Below are the key criteria that will determine an app's share of Gems in season 1.

Category:
    Apps are assessed across several weighted categories, with each app assigned a weight based on its primary category. For season 1, the specific weights are detailed below. If an app falls into multiple categories, the weight of its dominant category will be applied.

    Category                            Weight
    Bridges                             5
    CLOB DEX                            4
    Lending Markets / CDPs              4
    Fixed Yield / Yield Tokenization    4
    GambleFi                            3
    Perps                               3
    Derivatives                         3
    Yield                               2
    Gaming                              2
    Spot DEX                            2
    Tooling, Misc, and Payment          1
Sonic Native:
    Apps are assigned different weights depending on their level of exclusivity to Sonic:

    Weight 2: Exclusively available on Sonic

    Weight 1: Primarily on Sonic but accessible elsewhere

    Weight 0.5: Available across multiple chains

    Note: An app's Sonic-native weight cannot be upgraded during a season. However, if an app takes actions that reduce its Sonic nativeness, its weight will be reduced immediately and remain in effect for the following season as well.
Incentive:
    This assesses how effectively an app distributes its claimed S to its users. An app's incentive weight is determined by the percentage of its claimed S that was distributed to its users during the previous season.

    Incentive Weight = S Distributed to Users / S Claimed
    
    For example, if an app distributed 100% of its claimed S to its users, it’ll receive a weight of 1 in the next season, while distributing only 80% would give it a weight of 0.8.

    While there’s no requirement for apps to distribute a specific amount of their claimed S to users, it’s mandatory for all apps to publicly disclose the percentage they intend to share with their communities.

    This transparency allows users to make informed decisions about allocating their capital. Any instances of false communication or misuse of claimed S will result in blacklisting for subsequent seasons.

Final Gems Calculation
Apps will receive a pro-rata share of Sonic Gems based on their final weights, determined by the calculations below.

Gem Score = Category Weight × Sonic Native Weight × Incentive Weight(N/A in Season 1)

Point Score = Sonic Points Generated By App / Total Sonic Points Generated

Final Score = Gem Score × (1 + Point Score)

Share of Sonic Gems = (App Final Score / Total Final Score) × Total Gems


Gems Revocation Policy
The following actions by the app can cause their Sonic Gems to be revoked.

Incentivizing Project Tokens or NFTs with Gems
Allocating Gems as rewards for activities like holding, staking, or providing liquidity (LPing) for a project’s token or NFT. For apps that have a voting mechanism to direct emissions, Gems can be used as vote incentives for any pool other than those that contain the project's token.

Suspicious Distribution Practices
Distributing large quantities of Gems non-transparently, such as allocating them disproportionately to insiders or KOLs without clear disclosure.

Misrepresenting Gem Redistribution
Providing false information about the amount of claimed S being distributed to users during any season.
"""
