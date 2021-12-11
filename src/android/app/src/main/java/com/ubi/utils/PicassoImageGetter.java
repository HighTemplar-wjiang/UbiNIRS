// Ref: https://medium.com/@rajeefmk/android-textview-and-image-loading-from-url-part-1-a7457846abb6

package com.ubi.utils;

import android.app.Activity;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Point;
import android.graphics.drawable.BitmapDrawable;
import android.graphics.drawable.Drawable;
import android.text.Html;
import android.util.Log;
import android.view.Display;
import android.widget.TextView;

import com.squareup.picasso.Picasso;
import com.squareup.picasso.Target;
import com.ubi.NanoScan.R;
import com.ubi.UbiNIRS.NewScanActivity;

public class PicassoImageGetter implements Html.ImageGetter {

    private TextView mTextView = null;
    private Context mContext = null;

    public PicassoImageGetter() {

    }

    public PicassoImageGetter(Context context, TextView tvTarget) {
        this.mContext = context;
        this.mTextView = tvTarget;
    }

    @Override
    public Drawable getDrawable(String source) {
        BitmapDrawablePlaceHolder drawable = new BitmapDrawablePlaceHolder();
        String fullUrl = UbiNIRSUtils.getRESTfulAPI(
                UbiNIRSUtils.getDomainName(((NewScanActivity) mContext).getAppServerAddress()),
                source, null);
        fullUrl = fullUrl.replaceFirst("/$", "");

        // Log.
        Log.d("ImageGetter", fullUrl);

        Picasso.get()
                .load(fullUrl)
                .placeholder(R.drawable.img_loading)
                .into(drawable);
        return drawable;
    }

    private class BitmapDrawablePlaceHolder extends BitmapDrawable implements Target {

        protected Drawable mDrawable;

        @Override
        public void draw(final Canvas canvas) {
            if (this.mDrawable != null) {
                this.mDrawable.draw(canvas);
            }
        }

        public void setDrawable(Drawable drawable) {
            this.mDrawable = drawable;

            // Get image size.
            int width = drawable.getIntrinsicWidth();
            int height = drawable.getIntrinsicHeight();

            // Get display size.
            Point size = new Point();
            ((Activity) mContext).getWindowManager().getDefaultDisplay().getSize(size);
            double scale = 0.7;

            this.mDrawable.setBounds(0, 0, (int)(size.x * scale),
                    (int) (height * scale / width * size.x));
            if (mTextView != null) {
                mTextView.setText(mTextView.getText());
            }
        }

        @Override
        public void onBitmapLoaded(Bitmap bitmap, Picasso.LoadedFrom from) {
            this.setDrawable(new BitmapDrawable(mContext.getResources(), bitmap));
        }

        @Override
        public void onBitmapFailed(Exception e, Drawable errorDrawable) {

        }

        @Override
        public void onPrepareLoad(Drawable placeHolderDrawable) {

        }



    }

}
