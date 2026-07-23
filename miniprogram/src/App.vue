<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app'

onLaunch(() => undefined)
</script>

<style lang="scss">
page {
  min-height: 100%;
  color: #30251f;
  background: #f8f3eb;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

view,
text,
button,
input,
textarea,
image {
  box-sizing: border-box;
}

button::after {
  border: none;
}

.yy-page {
  min-height: 100vh;
  padding: 32rpx 32rpx 180rpx;
}

.yy-card {
  border: 1rpx solid #e7dbcf;
  border-radius: 36rpx;
  background: #fffdf9;
  box-shadow: 0 18rpx 48rpx rgba(77, 53, 38, 0.08);
}

.yy-kicker {
  color: #cf6447;
  font-size: 20rpx;
  font-weight: 700;
  letter-spacing: 4rpx;
  text-transform: uppercase;
}

.yy-title {
  margin-top: 12rpx;
  font-family: 'Songti SC', serif;
  font-size: 56rpx;
  font-weight: 700;
  line-height: 1.2;
}

.yy-primary {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 92rpx;
  border-radius: 46rpx;
  color: #ffffff;
  background: #30251f;
  font-size: 28rpx;
  font-weight: 600;
}

.yy-muted {
  color: #84746a;
}
</style>
